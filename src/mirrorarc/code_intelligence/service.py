# SPDX-License-Identifier: AGPL-3.0-or-later
"""Revision-bound repository analysis built on the existing repository identity contract."""
from __future__ import annotations

import dataclasses
import fcntl
import hashlib
import json
import os
import shutil
import shlex
import subprocess
import tempfile
import time
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from mirrorarc.code_intelligence.adapter import (
    PROVIDER_ENV,
    PROVIDER_NAME,
    SUPPORTED_VERSION,
    CodeGraphAdapter,
    CodeGraphError,
    find_codegraph,
)
from mirrorarc.mirrors import github_repos
from mirrorarc.relationships.model import EvidenceAnchor, canonical_json, stable_id
from mirrorarc.relationships.store import RelationshipStore, utc_now

CACHE_ROOT = Path(".mirrorarc/cache/code-intelligence")
REPO_CONFIG = Path("tools/repos.yml")
REPO_MANIFEST = Path("_meta/repo-manifest.json")
INSTALL_COMMAND = (
    "curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/v1.5.0/install.sh "
    "| CODEGRAPH_VERSION=v1.5.0 sh"
)
INSTALLER_SHA256 = "f4e90c6e0c1d2ac95a43fa6e82e4caf76fabdb18310afc72597314b58632e56c"
DARWIN_ARM64_ARCHIVE_SHA256 = "cf5ee435a6e44d097b2f98f2b7b8b9422bb1094844404efed82519c5da1af2cf"
MAX_ANALYSIS_FILES = 2000
MAX_SOURCE_BYTES = 128 * 1024 * 1024
MAX_SOURCE_FILE_BYTES = 16 * 1024 * 1024
MAX_EVIDENCE_FILES = 30
MAX_EVIDENCE_CHARS = 6000
MAX_RELATIONSHIPS = 100
SKIP_PARTS = {".git", ".codegraph", ".mirrorarc", "node_modules", "__pycache__", ".pytest_cache"}


class CodeIntelligenceError(ValueError):
    """A user-actionable repository intelligence failure."""

    def __init__(self, message: str, *, kind: str = "analysis-failure"):
        super().__init__(message)
        self.kind = kind


@dataclasses.dataclass(frozen=True)
class RepositorySpec:
    repo_id: str
    configured_repo: str
    note: str
    local_path: str
    repo_url: str
    aliases: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class Snapshot:
    repo: RepositorySpec
    source_path: Path
    snapshot_path: Path
    resolved_revision: str
    local_tree_hash: str
    revision_kind: str
    dirty: bool
    omissions: tuple[str, ...]

    @property
    def snapshot_id(self) -> str:
        value = hashlib.sha256(
            f"{self.resolved_revision}\0{self.local_tree_hash}".encode("utf-8")
        ).hexdigest()[:24]
        return f"snapshot_{value}"


def _read_json(path: Path, default: Any) -> Any:
    if not path.is_file() or path.is_symlink():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _write_json_atomic(path: Path, value: object) -> None:
    payload = (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    if path.is_file() and path.read_bytes() == payload:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        with temporary.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _acquire_analysis_lock(root: Path, repo_id: str, *, timeout_seconds: float = 30.0):
    """Serialize writes to one provider index and its publication pointers."""
    lock_path = root / CACHE_ROOT / repo_id / ".analysis.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+", encoding="utf-8")
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return handle
        except BlockingIOError:
            if time.monotonic() >= deadline:
                handle.close()
                raise CodeIntelligenceError(
                    "Another analysis is still updating this repository; retry after it finishes.",
                    kind="analysis-busy",
                )
            time.sleep(0.1)


def _release_analysis_lock(handle: Any) -> None:
    if handle is None:
        return
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    finally:
        handle.close()


def _repo_manifest_records(root: Path) -> list[dict[str, Any]]:
    value = _read_json(root / REPO_MANIFEST, {})
    records = value.get("records", []) if isinstance(value, dict) else []
    return [dict(item) for item in records if isinstance(item, dict)]


def configured_repositories(root: Path) -> list[RepositorySpec]:
    path = root / REPO_CONFIG
    if not path.is_file() or path.is_symlink():
        return []
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise CodeIntelligenceError(f"{REPO_CONFIG.as_posix()} is unreadable: {exc}", kind="repo-config") from exc
    raw = value.get("repos", []) if isinstance(value, dict) else []
    if not isinstance(raw, list):
        raise CodeIntelligenceError(f"{REPO_CONFIG.as_posix()} repos must be a list", kind="repo-config")
    results: list[RepositorySpec] = []
    seen: set[str] = set()
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise CodeIntelligenceError(f"repos[{index}] must be a mapping", kind="repo-config")
        repo = str(item.get("repo", "") or "").strip()
        note = str(item.get("note", "") or "").strip()
        if not repo or not note:
            raise CodeIntelligenceError(f"repos[{index}] requires repo and note", kind="repo-config")
        repo_id = github_repos.repo_id_for(repo, note)
        if repo_id in seen:
            raise CodeIntelligenceError(f"duplicate repository identity: {repo_id}", kind="repo-config")
        seen.add(repo_id)
        aliases = item.get("aliases", [])
        if not isinstance(aliases, list) or any(not isinstance(alias, str) for alias in aliases):
            raise CodeIntelligenceError(f"repos[{index}].aliases must be strings", kind="repo-config")
        results.append(RepositorySpec(
            repo_id=repo_id,
            configured_repo=repo,
            note=note,
            local_path=str(item.get("local_path", "") or "").strip(),
            repo_url=str(item.get("repo_url", "") or "").strip(),
            aliases=tuple(alias.strip() for alias in aliases if alias.strip()),
        ))
    return sorted(results, key=lambda item: (item.configured_repo, item.repo_id))


def select_repository(root: Path, requested: str | None) -> RepositorySpec:
    repos = configured_repositories(root)
    if not repos:
        raise CodeIntelligenceError(
            f"No governed repositories are configured in {REPO_CONFIG.as_posix()}.",
            kind="repo-not-configured",
        )
    if requested is None or not requested.strip():
        if len(repos) == 1:
            return repos[0]
        raise CodeIntelligenceError(
            "More than one repository is configured; pass --repo with a repository ID.",
            kind="repo-required",
        )
    target = requested.strip()
    matches = [
        item for item in repos
        if target in {
            item.repo_id,
            item.configured_repo,
            item.note,
            Path(item.note).stem,
            *item.aliases,
        }
    ]
    if len(matches) != 1:
        available = ", ".join(item.repo_id for item in repos)
        raise CodeIntelligenceError(
            f"Unknown or ambiguous repository '{target}'. Available IDs: {available}",
            kind="repo-not-found",
        )
    return matches[0]


def _safe_local_repository(root: Path, value: str) -> Path:
    rel = Path(value)
    if not value or rel.is_absolute() or ".." in rel.parts:
        raise CodeIntelligenceError("Configured local repository path must stay inside the vault.", kind="repo-boundary")
    path = (root / rel).resolve()
    if not path.is_relative_to(root) or not path.is_dir():
        raise CodeIntelligenceError(f"Configured local repository is unavailable: {value}", kind="repo-unavailable")
    cursor = root
    for part in rel.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise CodeIntelligenceError("Configured local repository must not traverse symlinks.", kind="repo-boundary")
    return path


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def _git_identity(path: Path) -> tuple[str, bool]:
    top = _git(path, "rev-parse", "--show-toplevel")
    if top.returncode != 0 or not top.stdout.strip() or Path(top.stdout.strip()).resolve() != path.resolve():
        return "", True
    head = _git(path, "rev-parse", "HEAD")
    if head.returncode != 0:
        return "", True
    status = _git(path, "status", "--porcelain", "--untracked-files=all")
    return head.stdout.strip(), status.returncode != 0 or bool(status.stdout.strip())


def _iter_source_files(path: Path) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    omissions: list[str] = []
    total_bytes = 0
    for directory, dirs, names in os.walk(path, followlinks=False):
        parent = Path(directory)
        for name in sorted(dirs):
            candidate = parent / name
            if candidate.is_symlink():
                omissions.append(f"Skipped symlink: {candidate.relative_to(path).as_posix()}")
        dirs[:] = sorted(name for name in dirs if name not in SKIP_PARTS and not (parent / name).is_symlink())
        for name in sorted(names):
            candidate = parent / name
            rel = candidate.relative_to(path)
            if candidate.is_symlink():
                omissions.append(f"Skipped symlink: {rel.as_posix()}")
                continue
            if not candidate.is_file():
                continue
            size = candidate.stat().st_size
            total_bytes += size
            if size > MAX_SOURCE_FILE_BYTES or total_bytes > MAX_SOURCE_BYTES:
                raise CodeIntelligenceError("Repository exceeds snapshot byte limits (16 MiB/file, 128 MiB/tree).", kind="repository-too-large")
            files.append(candidate)
            if len(files) > MAX_ANALYSIS_FILES:
                raise CodeIntelligenceError(
                    f"Repository exceeds the first-release limit of {MAX_ANALYSIS_FILES} files.",
                    kind="repository-too-large",
                )
    files.sort(key=lambda item: item.relative_to(path).as_posix())
    return files, omissions


def _tree_hash(path: Path) -> tuple[str, tuple[str, ...]]:
    digest = hashlib.sha256()
    files, omissions = _iter_source_files(path)
    for candidate in files:
        rel = candidate.relative_to(path).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        with candidate.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
        digest.update(b"\0")
    return "local-" + digest.hexdigest(), tuple(omissions)


def _copy_snapshot(source: Path, destination: Path) -> tuple[str, ...]:
    if destination.is_dir() and not destination.is_symlink():
        _files, omissions = _iter_source_files(source)
        return tuple(omissions)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    if temporary.exists():
        shutil.rmtree(temporary)
    temporary.mkdir(parents=True)
    _files, omissions = _iter_source_files(source)
    try:
        for candidate in _files:
            rel = candidate.relative_to(source)
            target = temporary / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(candidate, target)
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return tuple(omissions)


def _snapshot_from_source(root: Path, repo: RepositorySpec, source: Path, *, remote_revision: str = "") -> Snapshot:
    head, dirty = _git_identity(source)
    tree_hash, omissions = _tree_hash(source)
    revision = remote_revision or head or tree_hash
    revision_kind = "git-commit" if head and not dirty and not remote_revision else "local-tree"
    key = hashlib.sha256(f"{revision}\0{tree_hash}".encode("utf-8")).hexdigest()[:24]
    snapshot_path = root / CACHE_ROOT / repo.repo_id / "snapshots" / f"snapshot_{key}" / "source"
    copy_omissions = _copy_snapshot(source, snapshot_path)
    copied_hash, copied_omissions = _tree_hash(snapshot_path)
    final_hash, final_omissions = _tree_hash(source)
    if copied_hash != tree_hash or final_hash != tree_hash or copied_omissions:
        raise CodeIntelligenceError(
            "Snapshot identity mismatch: source changed during copy or cached snapshot was modified. Remove only the disposable code-intelligence cache and retry.",
            kind="snapshot-stale",
        )
    return Snapshot(
        repo=repo,
        source_path=source,
        snapshot_path=snapshot_path,
        resolved_revision=revision,
        local_tree_hash=tree_hash,
        revision_kind=revision_kind,
        dirty=dirty or not bool(head),
        omissions=tuple(sorted(set(omissions + copy_omissions))),
    )


def resolve_snapshot(root: Path, repo: RepositorySpec) -> Snapshot:
    if repo.local_path:
        source = _safe_local_repository(root, repo.local_path)
        return _snapshot_from_source(root, repo, source)
    token = github_repos.get_token()
    resolved, revision = github_repos.resolve_slug(
        {"repo": repo.configured_repo, "aliases": list(repo.aliases)}, token
    )
    if not resolved or not revision:
        raise CodeIntelligenceError(
            "The governed repository cannot be resolved. Check read-only GitHub access and run repo sync.",
            kind="repo-unavailable",
        )
    cloned, error = github_repos.clone(resolved, token, 50)
    if not cloned:
        raise CodeIntelligenceError(f"The governed repository snapshot could not be cloned: {error}", kind="repo-clone")
    try:
        source = Path(cloned).resolve()
        actual = _git(source, "rev-parse", "HEAD")
        if actual.returncode != 0 or actual.stdout.strip() != revision:
            raise CodeIntelligenceError("The cloned repository does not match the resolved revision.", kind="revision-mismatch")
        return _snapshot_from_source(root, repo, source, remote_revision=revision)
    finally:
        shutil.rmtree(cloned, ignore_errors=True)


def _safe_repo_path(value: str) -> str:
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts or path == PurePosixPath("."):
        raise CodeIntelligenceError(f"Repository path is unsafe: {value}", kind="source-boundary")
    return path.as_posix()


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _source_span(snapshot: Path, path_value: str, start: int, end: int) -> dict[str, Any]:
    rel = _safe_repo_path(path_value)
    path = snapshot / rel
    if path.is_symlink() or not path.is_file():
        raise CodeIntelligenceError(f"Evidence path is unavailable in the recorded snapshot: {rel}", kind="source-boundary")
    resolved = path.resolve()
    if not resolved.is_relative_to(snapshot.resolve()):
        raise CodeIntelligenceError(f"Evidence path escapes the recorded snapshot: {rel}", kind="source-boundary")
    raw = path.read_bytes()
    if b"\0" in raw:
        raise CodeIntelligenceError(f"Binary source omitted: {rel}", kind="unsupported-source")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CodeIntelligenceError(f"Non-UTF-8 source omitted: {rel}", kind="unsupported-source") from exc
    lines = text.splitlines(keepends=True)
    start_line = max(1, start or 1)
    end_line = min(end or start_line, len(lines))
    if start_line > end_line:
        raise CodeIntelligenceError(f"Source span is unavailable: {rel}:{start_line}-{end}", kind="source-boundary")
    excerpt = "".join(lines[start_line - 1:end_line])
    return {
        "path": rel, "hash": hashlib.sha256(raw).hexdigest(),
        "language": path.suffix.lower().lstrip("."),
        "line_ranges": [{"start": start_line, "end": end_line}],
        "excerpt": excerpt,
        "excerpt_hash": hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
        "truncated": False,
    }


def _merge_evidence(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Union exact source lines; included ranges describe only the exported text."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        grouped.setdefault(item["path"], []).append(item)
    merged = []
    for path, values in sorted(grouped.items()):
        lines: dict[int, str] = {}
        for value in values:
            if value["hash"] != values[0]["hash"]:
                raise CodeIntelligenceError("Evidence changed while selecting spans.", kind="snapshot-stale")
            content = iter(value["excerpt"].splitlines(keepends=True))
            for span in value["line_ranges"]:
                for number in range(span["start"], span["end"] + 1):
                    line = next(content, None)
                    if line is None or (number in lines and lines[number] != line):
                        raise CodeIntelligenceError("Evidence range does not match its text.", kind="evidence-mismatch")
                    lines[number] = line
            if next(content, None) is not None:
                raise CodeIntelligenceError("Evidence text exceeds its range.", kind="evidence-mismatch")
        ranges: list[dict[str, int]] = []
        excerpts = []
        used = 0
        for number, line in sorted(lines.items()):
            if used + len(line) > MAX_EVIDENCE_CHARS:
                break
            used += len(line)
            excerpts.append(line)
            if ranges and ranges[-1]["end"] + 1 == number:
                ranges[-1]["end"] = number
            else:
                ranges.append({"start": number, "end": number})
        excerpt = "".join(excerpts)
        merged.append({
            **values[0], "line_ranges": ranges, "excerpt": excerpt,
            "excerpt_hash": hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
            "truncated": len(excerpts) < len(lines),
            "requested_line_ranges": [span for value in values for span in value["line_ranges"]],
        })
    return merged


def _is_test_path(path: str) -> bool:
    name = PurePosixPath(path).name.lower()
    parts = {part.lower() for part in PurePosixPath(path).parts}
    return "tests" in parts or "test" in parts or name.startswith("test_") or ".test." in name or ".spec." in name


def _entry_points(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    preferred = []
    for item in files:
        name = PurePosixPath(item["path"]).name.lower()
        score = 0
        if name in {"main.py", "app.py", "cli.py", "index.ts", "index.js", "server.py"}:
            score += 100
        if item["path"].startswith(("scripts/", "src/")):
            score += 20
        if name == "__init__.py":
            score += 10
        score += min(int(item.get("symbol_count", 0)), 20)
        if score:
            preferred.append((score, item["path"], item))
    preferred.sort(key=lambda value: (-value[0], value[1]))
    return [item for _score, _path, item in preferred[:8]]


def _changed_from_base(source: Path, base: str) -> list[str]:
    if not base.strip():
        return []
    top = _git(source, "rev-parse", "--show-toplevel")
    if top.returncode != 0 or Path(top.stdout.strip()).resolve() != source.resolve():
        raise CodeIntelligenceError("--base requires a configured local Git repository.", kind="base-unavailable")
    verified = _git(source, "rev-parse", "--verify", "--end-of-options", f"{base}^{{commit}}")
    if verified.returncode != 0:
        raise CodeIntelligenceError(f"Base ref could not be resolved: {base}", kind="base-unavailable")
    # The analyzed snapshot is the working tree, so compare the base directly
    # to staged/unstaged files and include untracked paths. Disable renames so
    # both the removed and added paths remain visible.
    diff = _git(source, "diff", "--name-only", "-z", "--no-renames", verified.stdout.strip(), "--")
    untracked = _git(source, "ls-files", "--others", "--exclude-standard", "-z")
    if diff.returncode != 0 or untracked.returncode != 0:
        raise CodeIntelligenceError(f"Changed paths could not be resolved from base ref: {base}", kind="base-unavailable")
    return sorted({_safe_repo_path(item) for item in (diff.stdout + untracked.stdout).split("\0") if item})



def _analysis_paths(root: Path, repo_id: str) -> dict[str, Path]:
    base = root / CACHE_ROOT / repo_id
    return {
        "base": base,
        "analyses": base / "analyses",
        "latest": base / "latest.json",
        "state": base / "state.json",
    }


def _latest_analysis(root: Path, repo_id: str) -> dict[str, Any] | None:
    paths = _analysis_paths(root, repo_id)
    pointer = _read_json(paths["latest"], {})
    rel = str(pointer.get("analysis_path", "") or "") if isinstance(pointer, dict) else ""
    if not rel:
        return None
    candidate = root / rel
    if not candidate.resolve().is_relative_to((root / CACHE_ROOT).resolve()):
        return None
    value = _read_json(candidate, None)
    return value if isinstance(value, dict) else None


def _current_identity(root: Path, repo: RepositorySpec) -> tuple[str, str, bool]:
    if repo.local_path:
        source = _safe_local_repository(root, repo.local_path)
        head, dirty = _git_identity(source)
        tree, _omissions = _tree_hash(source)
        return head or tree, tree, dirty or not bool(head)
    for record in _repo_manifest_records(root):
        if record.get("repo_id") == repo.repo_id:
            revision = str(record.get("last_commit", "") or "")
            return revision, "", False
    return "", "", False


def _freshness(root: Path, repo: RepositorySpec, analysis: dict[str, Any]) -> tuple[str, str]:
    try:
        revision, tree, dirty = _current_identity(root, repo)
    except CodeIntelligenceError as exc:
        return "stale", str(exc)
    if not revision:
        return "stale", "Current repository revision is unavailable."
    if revision != analysis.get("resolved_revision"):
        return "stale", "The governed repository revision has changed since analysis."
    recorded_tree = str(analysis.get("local_tree_hash", "") or "")
    if tree and recorded_tree and tree != recorded_tree:
        return "stale", "The local repository tree has changed since analysis."
    if dirty:
        return "local-uncommitted", "This result is bound to a local uncommitted tree hash."
    return "current", ""


def _record_failure(root: Path, repo_id: str, error: Exception) -> None:
    if isinstance(error, CodeGraphError):
        detail = error.as_dict()
    elif isinstance(error, CodeIntelligenceError):
        detail = {"kind": error.kind, "message": str(error)}
    else:
        detail = {"kind": "analysis-failure", "message": str(error)}
    _write_json_atomic(_analysis_paths(root, repo_id)["state"], {
        "schema_version": 1,
        "repo_id": repo_id,
        "freshness_state": "failed",
        "updated_at": utc_now(),
        "error": detail,
    })


def _register_analysis(root: Path, analysis: dict[str, Any], analysis_rel: str) -> None:
    store = RelationshipStore(root)
    graph = store.export(current_only=False)
    artifacts = {item["artifact_id"]: item for item in graph["artifacts"]}
    repo_id = analysis["repo_id"]
    repo_artifact = artifacts.get(repo_id)
    if repo_artifact is None:
        repo_artifact = {
            "artifact_id": repo_id,
            "artifact_kind": "repository",
            "layer": "L0",
            "path": analysis["configured_repo"],
            "title": analysis["configured_repo"],
            "domain": "sources",
            "content_hash": analysis["local_tree_hash"] or analysis["resolved_revision"],
            "lifecycle_state": "current",
            "authority": "authoritative",
            "metadata": {"manifest": "repository", "source_type": analysis["revision_kind"]},
        }
        store.upsert_artifact(repo_artifact)
    artifact = {
        "artifact_id": analysis["analysis_id"],
        "artifact_kind": "code-evidence",
        "layer": "derived",
        "path": analysis_rel,
        "title": f"Code evidence · {analysis['configured_repo']}",
        "domain": str(repo_artifact.get("domain", "sources") or "sources"),
        "content_hash": analysis["analysis_hash"],
        "lifecycle_state": analysis["freshness_state"],
        "authority": "derived",
        "metadata": {
            "analysis_kind": analysis["analysis_kind"],
            "repo_id": repo_id,
            "resolved_revision": analysis["resolved_revision"],
            "provider_version": analysis["provider_version"],
            "warning_count": len(analysis["warnings"]),
            "omission_count": len(analysis["omissions"]),
        },
    }
    store.upsert_artifact(artifact)
    store.put_relationship(
        source_artifact_id=analysis["analysis_id"],
        target_artifact_id=repo_id,
        relationship_type="DEPENDS_ON",
        method="code-analysis",
        method_version=analysis["provider_version"],
        state="accepted",
        source_hash=analysis["analysis_hash"],
        target_hash=analysis["local_tree_hash"] or analysis["resolved_revision"],
        evidence=[EvidenceAnchor(
            artifact_id=analysis["analysis_id"],
            selector_type="repository-revision",
            selector_value=analysis["resolved_revision"],
            source_hash=analysis["analysis_hash"],
        )],
    )
    with store.connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO dependency_edges(dependent_artifact_id,dependency_artifact_id,dependency_kind,dependency_hash,created_at) VALUES (?,?,?,?,?)",
            (
                analysis["analysis_id"], repo_id, "code-analysis-input",
                analysis["local_tree_hash"] or analysis["resolved_revision"], utc_now(),
            ),
        )


def analyze_repository(
    root: Path,
    repo_value: str,
    *,
    symbol: str = "",
    base: str = "",
    changed_paths: list[str] | None = None,
    binary: str | Path | None = None,
) -> dict[str, Any]:
    root = root.expanduser().resolve()
    repo = select_repository(root, repo_value)
    lock_handle = None
    try:
        lock_handle = _acquire_analysis_lock(root, repo.repo_id)
        if base.strip() and not repo.local_path:
            raise CodeIntelligenceError(
                "--base is available only for a configured local Git repository; use --changed-path for a remote snapshot.",
                kind="base-unavailable",
            )
        adapter = CodeGraphAdapter(binary)
        version = adapter.version()
        if version != SUPPORTED_VERSION:
            raise CodeIntelligenceError(
                f"Supported local analysis helper version is {SUPPORTED_VERSION}; found {version}.",
                kind="provider-version",
            )
        snapshot = resolve_snapshot(root, repo)
        requested_paths = [_safe_repo_path(item) for item in (changed_paths or [])]
        requested_paths.extend(_changed_from_base(snapshot.source_path, base))
        requested_paths = sorted(set(requested_paths))
        provider_status = adapter.ensure_index(snapshot.snapshot_path)
        files = adapter.files(snapshot.snapshot_path)
        file_map = {item["path"]: item for item in files}
        languages: dict[str, int] = {}
        for item in files:
            language = item["language"] or "unknown"
            languages[language] = languages.get(language, 0) + 1

        query_results: list[dict[str, Any]] = []
        selected_symbol: dict[str, Any] | None = None
        callers: list[dict[str, Any]] = []
        callees: list[dict[str, Any]] = []
        impact: dict[str, Any] = {"direct": [], "transitive": []}
        relationships: list[dict[str, Any]] = []
        evidence: list[dict[str, Any]] = []
        warnings: list[str] = []
        omissions = list(snapshot.omissions)

        if symbol.strip():
            query_results = adapter.query(snapshot.snapshot_path, symbol.strip(), limit=20)
            if query_results:
                exact = [
                    item for item in query_results
                    if item["name"] == symbol.strip() or item["qualified_name"] == symbol.strip()
                ]
                selected_symbol = (exact or query_results)[0]
                evidence.append(_source_span(
                    snapshot.snapshot_path,
                    selected_symbol["path"],
                    selected_symbol["start_line"],
                    selected_symbol["end_line"],
                ))
                caller_result = adapter.callers(snapshot.snapshot_path, selected_symbol["qualified_name"] or selected_symbol["name"])
                callee_result = adapter.callees(snapshot.snapshot_path, selected_symbol["qualified_name"] or selected_symbol["name"])
                impact_raw = adapter.impact(snapshot.snapshot_path, selected_symbol["qualified_name"] or selected_symbol["name"], depth=3)
                callers = caller_result["callers"][:20]
                callees = callee_result["callees"][:20]
                direct_keys = {(item["path"], item["start_line"], item["name"]) for item in callers + callees}
                affected = [
                    item for item in impact_raw["affected"]
                    if not (item["path"] == selected_symbol["path"] and item["name"] == selected_symbol["name"])
                ]
                impact = {
                    "direct": [item for item in affected if (item["path"], item["start_line"], item["name"]) in direct_keys],
                    "transitive": [item for item in affected if (item["path"], item["start_line"], item["name"]) not in direct_keys],
                }
                for item in callers:
                    relationships.append({
                        "source": item, "target": selected_symbol, "kind": "calls",
                        "provenance": "provider-callers", "depth": 1,
                    })
                for item in callees:
                    relationships.append({
                        "source": selected_symbol, "target": item, "kind": "calls",
                        "provenance": "provider-callees", "depth": 1,
                    })
                for item in (callers + callees + impact["transitive"])[:MAX_EVIDENCE_FILES - 1]:
                    try:
                        evidence.append(_source_span(
                            snapshot.snapshot_path, item["path"], item["start_line"], item["start_line"]
                        ))
                    except CodeIntelligenceError as exc:
                        omissions.append(str(exc))
            else:
                warnings.append(f"No indexed symbol matched '{symbol.strip()}'.")

        affected_tests: list[dict[str, str]] = []
        affected_result: dict[str, Any] = {
            "changed_files": requested_paths,
            "affected_tests": [],
            "total_dependents_traversed": 0,
        }
        if requested_paths:
            affected_result = adapter.affected(snapshot.snapshot_path, requested_paths, depth=5)
            affected_tests.extend({"path": item, "basis": "provider-affected", "confidence": "medium"} for item in affected_result["affected_tests"])
        for item in impact["direct"] + impact["transitive"]:
            if _is_test_path(item["path"]):
                affected_tests.append({"path": item["path"], "basis": "symbol-impact", "confidence": "medium"})
        if requested_paths and not affected_tests:
            for changed in requested_paths[:10]:
                stem = PurePosixPath(changed).stem
                try:
                    results = adapter.query(snapshot.snapshot_path, stem, limit=50)
                except CodeGraphError as exc:
                    omissions.append(f"Candidate test fallback failed for {changed}: {exc}")
                    continue
                for item in results:
                    if _is_test_path(item["path"]):
                        affected_tests.append({
                            "path": item["path"],
                            "basis": "provider-search-heuristic",
                            "confidence": "low",
                        })
            if affected_tests:
                warnings.append(
                    "The provider did not return affected tests for these paths; listed tests are low-confidence candidates from indexed references."
                )
        unique_tests: dict[str, dict[str, str]] = {}
        confidence_order = {"high": 0, "medium": 1, "low": 2}
        for item in affected_tests:
            current = unique_tests.get(item["path"])
            if current is None or confidence_order[item["confidence"]] < confidence_order[current["confidence"]]:
                unique_tests[item["path"]] = item
        affected_tests = [unique_tests[key] for key in sorted(unique_tests)]
        if affected_tests:
            warnings.append(
                "Affected tests are candidates only; the repository's normal test gate remains authoritative."
            )

        for changed in requested_paths:
            if changed in file_map:
                try:
                    evidence.append(_source_span(snapshot.snapshot_path, changed, 1, min(40, 10**9)))
                except CodeIntelligenceError as exc:
                    omissions.append(str(exc))
            else:
                omissions.append(f"Changed path is not present in the recorded snapshot: {changed}")
        evidence = _merge_evidence(evidence)
        if len(evidence) > MAX_EVIDENCE_FILES:
            omissions.extend(f"Evidence file budget: {item['path']}" for item in evidence[MAX_EVIDENCE_FILES:])
            evidence = evidence[:MAX_EVIDENCE_FILES]
        for item in evidence:
            if item["truncated"]:
                omissions.append(f"Evidence spans truncated: {item['path']}")
        if _tree_hash(snapshot.snapshot_path)[0] != snapshot.local_tree_hash:
            raise CodeIntelligenceError("Snapshot changed during provider analysis.", kind="snapshot-stale")
        call_path: list[dict[str, Any]] = []
        if selected_symbol:
            if callers:
                call_path.append(callers[0])
            call_path.append({key: selected_symbol[key] for key in ("name", "kind", "path", "start_line")})
            if callees:
                call_path.append(callees[0])

        request = {
            "symbol": symbol.strip(),
            "base": base.strip(),
            "changed_paths": sorted(set(changed_paths or [])),
            "resolved_changed_paths": requested_paths,
            "base_semantics": "base-to-working-tree-including-untracked",
        }
        analysis_kind = "change" if requested_paths else "symbol" if symbol.strip() else "overview"
        stable_payload = {
            "repo_id": repo.repo_id,
            "resolved_revision": snapshot.resolved_revision,
            "local_tree_hash": snapshot.local_tree_hash,
            "provider_name": PROVIDER_NAME,
            "provider_version": version,
            "analysis_kind": analysis_kind,
            "request": request,
            "overview": {
                "file_count": len(files),
                "languages": dict(sorted(languages.items())),
                "key_entry_points": _entry_points(files),
            },
            "files": evidence,
            "symbols": [selected_symbol] if selected_symbol else [],
            "relationships": relationships[:MAX_RELATIONSHIPS],
            "call_path": call_path,
            "impact": impact,
            "affected_tests": affected_tests,
            "warnings": sorted(set(warnings)),
            "omissions": sorted(set(omissions)),
        }
        freshness_state = "local-uncommitted" if snapshot.dirty else "current"
        if snapshot.dirty:
            stable_payload["warnings"] = sorted(set(stable_payload["warnings"] + [
                "This analysis is bound to a local tree hash, not a clean immutable commit."
            ]))
        analysis_hash = hashlib.sha256(canonical_json(stable_payload).encode("utf-8")).hexdigest()
        analysis_id = stable_id(
            "code_analysis",
            repo.repo_id,
            snapshot.resolved_revision,
            snapshot.local_tree_hash,
            analysis_kind,
            canonical_json(request),
        )
        paths = _analysis_paths(root, repo.repo_id)
        analysis_path = paths["analyses"] / f"{analysis_id}.json"
        existing = _read_json(analysis_path, {})
        created_at = str(existing.get("created_at", "") or utc_now()) if isinstance(existing, dict) else utc_now()
        analysis = {
            "schema_version": 1,
            "analysis_id": analysis_id,
            "analysis_hash": analysis_hash,
            "repo_id": repo.repo_id,
            "configured_repo": repo.configured_repo,
            "resolved_revision": snapshot.resolved_revision,
            "local_tree_hash": snapshot.local_tree_hash,
            "revision_kind": snapshot.revision_kind,
            "provider_name": PROVIDER_NAME,
            "provider_version": version,
            "analysis_kind": analysis_kind,
            "request": request,
            "created_at": created_at,
            "freshness_state": freshness_state,
            "provider_summary": {
                "file_count": provider_status["file_count"],
                "node_count": provider_status["node_count"],
                "edge_count": provider_status["edge_count"],
                "index_state": provider_status["index_state"],
            },
            **{key: stable_payload[key] for key in (
                "overview", "files", "symbols", "relationships", "call_path", "impact",
                "affected_tests", "warnings", "omissions",
            )},
            "next_action": {
                "label": "Refresh the portable Catalog",
                "command": f"mirrorarc --root {root} catalog --html",
            },
        }
        analysis_rel = analysis_path.relative_to(root).as_posix()
        _write_json_atomic(analysis_path, analysis)
        _write_json_atomic(paths["latest"], {
            "schema_version": 1,
            "repo_id": repo.repo_id,
            "analysis_id": analysis_id,
            "analysis_path": analysis_rel,
        })
        _write_json_atomic(paths["state"], {
            "schema_version": 1,
            "repo_id": repo.repo_id,
            "freshness_state": freshness_state,
            "updated_at": utc_now(),
            "analysis_id": analysis_id,
        })
        _register_analysis(root, analysis, analysis_rel)
        return analysis
    except (CodeGraphError, CodeIntelligenceError) as exc:
        _record_failure(root, repo.repo_id, exc)
        raise
    finally:
        _release_analysis_lock(lock_handle)


def doctor_report(
    root: Path,
    repo_value: str | None = None,
    *,
    binary: str | Path | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    root = root.expanduser().resolve()
    found = find_codegraph(binary)
    retry_repo = f" --repo {repo_value}" if repo_value else ""
    retry = f"mirrorarc --root {root} code doctor{retry_repo}"
    base = {
        "schema_version": 1,
        "command": "code doctor",
        "supported_version": SUPPORTED_VERSION,
        "install_command": INSTALL_COMMAND,
        "retry_command": retry,
    }
    if found is None:
        return {
            **base,
            "verdict": "Setup needed",
            "status": "setup-needed",
            "message": "The optional local analysis helper is not installed or not on PATH.",
            "next_action": INSTALL_COMMAND,
        }
    try:
        adapter = CodeGraphAdapter(found)
        version = adapter.version()
    except CodeGraphError as exc:
        return {
            **base,
            "verdict": "Attention",
            "status": "attention",
            "message": str(exc),
            "next_action": retry,
            "error": exc.as_dict() if verbose else {"kind": exc.kind},
        }
    if version != SUPPORTED_VERSION:
        return {
            **base,
            "verdict": "Attention",
            "status": "attention",
            "message": f"Supported version is {SUPPORTED_VERSION}; found {version}.",
            "next_action": INSTALL_COMMAND,
            "provider_version": version,
        }
    try:
        repo = select_repository(root, repo_value)
        if repo.local_path:
            _safe_local_repository(root, repo.local_path)
        elif not any(record.get("repo_id") == repo.repo_id and record.get("last_commit") for record in _repo_manifest_records(root)):
            raise CodeIntelligenceError(
                "Run repository sync first so MirrorArc can bind analysis to a governed revision.",
                kind="repo-not-synced",
            )
    except CodeIntelligenceError as exc:
        return {
            **base,
            "verdict": "Attention",
            "status": "attention",
            "message": str(exc),
            "next_action": f"mirrorarc --root {root} sync --json",
            "error": {"kind": exc.kind},
        }
    report = {
        **base,
        "verdict": "Ready",
        "status": "ready",
        "message": "Local repository analysis is ready.",
        "repo_id": repo.repo_id,
        "provider_version": version,
        "next_action": f"mirrorarc --root {root} code analyze --repo {repo.repo_id}",
    }
    if verbose:
        report["diagnostics"] = {
            "provider": PROVIDER_NAME,
            "provider_path": str(found),
            "managed_environment": dict(PROVIDER_ENV),
            "verified_installer_sha256": INSTALLER_SHA256,
            "verified_darwin_arm64_archive_sha256": DARWIN_ARM64_ARCHIVE_SHA256,
        }
    return report


def status_report(root: Path, repo_value: str | None = None) -> dict[str, Any]:
    root = root.expanduser().resolve()
    repos = [select_repository(root, repo_value)] if repo_value else configured_repositories(root)
    items: list[dict[str, Any]] = []
    for repo in repos:
        latest = _latest_analysis(root, repo.repo_id)
        state = _read_json(_analysis_paths(root, repo.repo_id)["state"], {})
        if latest is None:
            failure = state.get("error") if isinstance(state, dict) and state.get("freshness_state") == "failed" else None
            freshness = "failed" if failure else "no-analysis"
            reason = str((failure or {}).get("message", "") or "No repository analysis has been run.")
            items.append({
                "repo_id": repo.repo_id,
                "configured_repo": repo.configured_repo,
                "freshness_state": freshness,
                "reason": reason,
                "analysis": None,
                "next_action": f"mirrorarc --root {root} code analyze --repo {repo.repo_id}",
            })
            continue
        freshness, reason = _freshness(root, repo, latest)
        if isinstance(state, dict) and state.get("freshness_state") == "failed" and state.get("analysis_id") != latest.get("analysis_id"):
            freshness = "failed"
            reason = str((state.get("error") or {}).get("message", "") or "The latest refresh failed; the prior valid analysis was retained.")
        items.append({
            "repo_id": repo.repo_id,
            "configured_repo": repo.configured_repo,
            "freshness_state": freshness,
            "reason": reason,
            "analysis": {
                "analysis_id": latest.get("analysis_id"),
                "analysis_kind": latest.get("analysis_kind"),
                "resolved_revision": latest.get("resolved_revision"),
                "local_tree_hash": latest.get("local_tree_hash"),
                "created_at": latest.get("created_at"),
                "warnings": len(latest.get("warnings", [])),
                "omissions": len(latest.get("omissions", [])),
            },
            "next_action": (
                f"mirrorarc --root {root} code analyze --repo {repo.repo_id}"
                if freshness in {"stale", "failed"}
                else f"mirrorarc --root {root} catalog --html"
            ),
        })
    return {
        "schema_version": 1,
        "command": "code status",
        "items": items,
        "summary": {
            "repositories": len(items),
            "current": sum(1 for item in items if item["freshness_state"] in {"current", "local-uncommitted"}),
            "attention": sum(1 for item in items if item["freshness_state"] not in {"current", "local-uncommitted"}),
        },
    }


def _catalog_analysis(analysis: dict[str, Any], *, include_excerpts: bool) -> dict[str, Any]:
    value = json.loads(json.dumps(analysis))
    for item in value.get("files", []):
        if not include_excerpts:
            item.pop("excerpt", None)
            item["excerpt_included"] = False
        else:
            item["excerpt_included"] = True
    return value


def catalog_report(root: Path, *, include_excerpts: bool = False) -> dict[str, Any]:
    root = root.expanduser().resolve()
    status = status_report(root)
    repositories = []
    for item in status["items"]:
        latest = _latest_analysis(root, item["repo_id"])
        request = (latest or {}).get("request", {})
        command = ["mirrorarc", "--root", ".", "code", "analyze", f"--repo={item['repo_id']}"]
        for option in ("symbol", "base"):
            if request.get(option):
                command.append(f"--{option}={request[option]}")
        command.extend(f"--changed-path={path}" for path in request.get("changed_paths", []))
        repositories.append({
            **item,
            "analysis": _catalog_analysis(latest, include_excerpts=include_excerpts) if latest else None,
            "next_action": shlex.join(command),
            "context_command": shlex.join(command + ["--context", "frozen"]),
        })
    return {
        "schema_version": 1,
        "content_included": bool(include_excerpts),
        "repositories": repositories,
        "summary": status["summary"],
        "policy": (
            "Bounded code excerpts are included for local review. Treat this file as sensitive."
            if include_excerpts
            else "Metadata-only. Source bodies and code excerpts are excluded."
        ),
    }
