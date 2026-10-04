# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only source/L1/L2 inventory and anti-proliferation checks.

This module deliberately derives its report from the existing source/repository manifests and the
shared Markdown classifier.  It does not create another registry or lifecycle authority.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - package dependency
    yaml = None

from mirrorarc.migration import markdown_inventory, markdown_summary
from mirrorarc.runtime_profile import configured_office_mirror_root, load_profile_mapping

SOURCE_MANIFEST_REL = Path("_meta/source-manifest.json")
REPO_MANIFEST_REL = Path("_meta/repo-manifest.json")
MIRROR_CONFIG_REL = Path("_meta/mirror-config.yml")
REPO_CONFIG_REL = Path("tools/repos.yml")
OPAQUE_EXTENSIONS = {".doc", ".docx", ".pdf", ".pptx", ".xlsx"}
NATIVE_READABLE_EXTENSIONS = {".csv", ".json", ".md", ".txt", ".tsv", ".yaml", ".yml"}
INACTIVE_STATES = {"source_missing", "repo_unconfigured", "superseded", "archived"}
DECLARED_FAILURE_STATES = {"conflict", "error", "manual_modification", "unsupported", "unreachable"}
EXCLUDED_PARTS = {
    ".git", ".mirrorarc", ".vaultwright", "node_modules", "_archive", "_backup",
    "_deprecated", "_meta", "_mirrors", "_templates", "_tmp", "tools",
}


def stable_projection_id(source_id: str) -> str:
    return f"l1_{hashlib.sha256(source_id.encode('utf-8')).hexdigest()[:20]}"


def native_source_id(path: str) -> str:
    return f"native_{hashlib.sha256(path.encode('utf-8')).hexdigest()[:20]}"


def _load_json_records(root: Path, rel: Path) -> tuple[list[dict[str, Any]], list[str]]:
    path = root / rel
    if not path.exists():
        return [], []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], [f"{rel.as_posix()}: invalid JSON ({exc.__class__.__name__})"]
    if not isinstance(value, dict) or not isinstance(value.get("records", []), list):
        return [], [f"{rel.as_posix()}: records must be a list"]
    return [dict(item) for item in value.get("records", []) if isinstance(item, dict)], []


def _profile_policy(root: Path) -> tuple[set[str], str]:
    profile = load_profile_mapping(root)
    folders: set[str] = set()
    domains = profile.get("domains") if isinstance(profile, dict) else None
    if isinstance(domains, dict):
        for value in domains.values():
            if isinstance(value, dict) and isinstance(value.get("folder"), str):
                folders.add(value["folder"])
    policy = profile.get("policy_defaults") if isinstance(profile, dict) else None
    mode = str((policy or {}).get("native_source_mode", "direct") or "direct") if isinstance(policy, dict) else "direct"
    return folders, mode


def _excluded(rel: Path, *, mirror_root: Path) -> bool:
    if any(part.startswith(".") or part in EXCLUDED_PARTS for part in rel.parts):
        return True
    return bool(mirror_root.parts and rel.parts[: len(mirror_root.parts)] == mirror_root.parts)


def _include_pdf(root: Path) -> bool:
    path = root / MIRROR_CONFIG_REL
    if not path.exists() or yaml is None:
        return False
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return False
    return bool(value.get("include_pdf")) if isinstance(value, dict) else False


def _configured_repositories(root: Path) -> list[dict[str, str]]:
    path = root / REPO_CONFIG_REL
    if not path.exists() or yaml is None:
        return []
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return []
    repos = value.get("repos", []) if isinstance(value, dict) else []
    result: list[dict[str, str]] = []
    for item in repos if isinstance(repos, list) else []:
        if not isinstance(item, dict):
            continue
        repo = str(item.get("repo", "") or "").strip()
        note = str(item.get("note", "") or "").strip()
        if repo and note:
            digest = hashlib.sha256(f"{repo}\0{note}".encode("utf-8")).hexdigest()[:20]
            result.append({"source_id": f"repo_{digest}", "path": str(item.get("local_path") or repo), "format": "repository"})
    return result


def _view_state_counts(root: Path) -> dict[str, int] | None:
    for rel in (Path(".mirrorarc/state.sqlite"), Path(".vaultwright/state.sqlite")):
        path = root / rel
        if not path.exists():
            continue
        try:
            conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='knowledge_views'"
            ).fetchone()
            if not exists:
                conn.close()
                return None
            counts = {str(row[0]): int(row[1]) for row in conn.execute(
                "SELECT state,COUNT(*) FROM knowledge_views GROUP BY state"
            )}
            conn.close()
            return counts
        except sqlite3.Error:
            return None
    return None


def build_inventory(root: Path) -> dict[str, Any]:
    root = root.expanduser().resolve()
    mirror_root = configured_office_mirror_root(root)
    content_roots, native_mode = _profile_policy(root)
    include_pdf = _include_pdf(root)
    markdown_items = markdown_inventory(root)
    markdown_counts = markdown_summary(markdown_items)
    markdown_by_path = {str(item["path"]): item for item in markdown_items}

    opaque_sources: list[dict[str, str]] = []
    native_sources: list[dict[str, str]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(root)
        if _excluded(rel, mirror_root=mirror_root):
            continue
        if content_roots and (not rel.parts or rel.parts[0] not in content_roots):
            continue
        suffix = path.suffix.lower()
        if suffix in OPAQUE_EXTENSIONS and (suffix != ".pdf" or include_pdf):
            opaque_sources.append({"path": rel.as_posix(), "format": suffix.lstrip(".")})
        elif suffix in NATIVE_READABLE_EXTENSIONS:
            if suffix == ".md":
                category = str(markdown_by_path.get(rel.as_posix(), {}).get("category", "unknown"))
                if category != "authoritative_markdown_source":
                    continue
            native_sources.append({
                "source_id": native_source_id(rel.as_posix()),
                "path": rel.as_posix(),
                "format": suffix.lstrip("."),
                "projection_policy": native_mode,
            })

    source_records, errors = _load_json_records(root, SOURCE_MANIFEST_REL)
    repo_records, repo_errors = _load_json_records(root, REPO_MANIFEST_REL)
    errors.extend(repo_errors)
    current_source_records = [
        record for record in source_records
        if str(record.get("lifecycle_state", "clean") or "clean") not in INACTIVE_STATES
    ]
    current_repo_records = [
        record for record in repo_records
        if str(record.get("lifecycle_state", "clean") or "clean") not in INACTIVE_STATES
    ]
    current_source_paths = {
        str(record.get("current_source_path", "") or "").strip()
        for record in current_source_records
    }
    for source in opaque_sources:
        if source["path"] not in current_source_paths:
            errors.append(f"office:{source['path']}: active opaque source has no manifest identity or L1 disposition")

    projection_claims: dict[str, list[str]] = {}
    source_claims: dict[str, list[str]] = {}
    mirror_claims: dict[str, list[str]] = {}
    active_l1: list[dict[str, str]] = []
    conversion_failures = 0
    for kind, records, id_key, path_key in (
        ("office", current_source_records, "source_id", "mirror_path"),
        ("repository", current_repo_records, "repo_id", "note_path"),
    ):
        for index, record in enumerate(records):
            identity = str(record.get(id_key, "") or "").strip()
            label = f"{kind}:{identity or index}"
            if not identity:
                errors.append(f"{label}: missing {id_key}")
                continue
            source_claims.setdefault(f"{kind}:{identity}", []).append(label)
            projection_id = str(record.get("projection_id", "") or stable_projection_id(identity)).strip()
            projection_claims.setdefault(projection_id, []).append(label)
            rel = str(record.get(path_key, "") or "").strip()
            if rel:
                mirror_claims.setdefault(rel, []).append(label)
            state = str(record.get("lifecycle_state", "clean") or "clean")
            if state in DECLARED_FAILURE_STATES or (kind == "office" and str(record.get("source_format", "")) == "doc"):
                conversion_failures += 1
                continue
            if not rel or not (root / rel).is_file():
                errors.append(f"{label}: active source has no current L1 projection file")
                continue
            active_l1.append({
                "projection_id": projection_id,
                "source_id": identity,
                "path": rel,
                "source_kind": kind,
                "identity_origin": "manifest" if record.get("projection_id") else "deterministic_compatibility",
            })

    for identity, claims in sorted(source_claims.items()):
        if len(claims) > 1:
            errors.append(f"{identity}: {len(claims)} active manifest records claim one source identity")
    for projection_id, claims in sorted(projection_claims.items()):
        if len(claims) > 1:
            errors.append(f"{projection_id}: projection identity is claimed by {len(claims)} active sources")
    for rel, claims in sorted(mirror_claims.items()):
        if len(claims) > 1:
            errors.append(f"{rel}: L1 path is claimed by {len(claims)} active sources")

    owned_l1_paths = set(mirror_claims)
    classified_l1_paths = {
        str(item["path"]) for item in markdown_items if item.get("category") == "l1_projection"
    }
    for rel in sorted(classified_l1_paths - owned_l1_paths):
        errors.append(f"{rel}: orphan L1 projection is not owned by a current manifest record")

    configured_repos = _configured_repositories(root)
    current_repo_ids = {str(record.get("repo_id", "") or "").strip() for record in current_repo_records}
    for source in configured_repos:
        if source["source_id"] not in current_repo_ids:
            errors.append(f"repository:{source['path']}: configured source has no manifest identity or L1 disposition")
    view_counts = _view_state_counts(root)
    summary = {
        "authoritative_source_records": len(opaque_sources) + len(native_sources) + len(configured_repos),
        "opaque_sources_requiring_l1": len(opaque_sources) + len(configured_repos),
        "native_readable_sources": len(native_sources),
        "native_sources_requiring_projection": len(native_sources) if native_mode in {"isolated_projection", "immutable_projection"} else 0,
        "active_l1_projections": len(active_l1),
        "declared_conversion_failures": conversion_failures,
        "l2_generated_views": view_counts.get("generated", 0) if view_counts is not None else markdown_counts["l2_generated_view"],
        "l2_reviewed_views": view_counts.get("reviewed", 0) if view_counts is not None else markdown_counts["l2_reviewed_view"],
        "l2_stale_views": view_counts.get("stale", 0) if view_counts is not None else sum(
            1 for item in markdown_items
            if item.get("category") == "l2_reviewed_view" and item.get("view_state") == "stale"
        ),
        "unexplained_markdown": markdown_counts["unknown"],
        "legacy_curated_derivatives": markdown_counts["legacy_curated_derivative"],
        "cardinality_errors": len(errors),
    }
    return {
        "schema_version": 1,
        "root": str(root),
        "native_source_mode": native_mode,
        "summary": summary,
        "opaque_sources": opaque_sources,
        "native_sources": native_sources,
        "repository_sources": configured_repos,
        "active_l1_projections": active_l1,
        "markdown": {"summary": markdown_counts, "items": markdown_items},
        "errors": errors,
    }


def render_text(report: dict[str, Any]) -> str:
    summary = report["summary"]
    keys = (
        "authoritative_source_records", "opaque_sources_requiring_l1", "native_readable_sources",
        "native_sources_requiring_projection", "active_l1_projections", "declared_conversion_failures",
        "l2_generated_views", "l2_reviewed_views", "l2_stale_views", "unexplained_markdown",
        "legacy_curated_derivatives", "cardinality_errors",
    )
    lines = [f"# MirrorArc knowledge inventory — {report['root']}", ""]
    lines.extend(f"- {key}: {summary[key]}" for key in keys)
    lines.append(f"- native_source_mode: {report['native_source_mode']}")
    if report["errors"]:
        lines.extend(["", "## Cardinality and ownership errors", *[f"- {item}" for item in report["errors"]]])
    return "\n".join(lines) + "\n"
