# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deterministic, read-only navigation models for local Vaultwright vaults.

The navigation model deliberately contains note metadata rather than note bodies.  A
server that needs to display a note must make a second, guarded ``read_document``
call.  That split keeps inventory endpoints small and avoids turning the navigation
index into another copy of the user's knowledge base.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
import hashlib
from pathlib import Path, PurePosixPath
import os
import re
from typing import Any, Iterable
from urllib.parse import unquote, urlsplit

import yaml

from vaultwright.runtime_profile import (
    configured_office_mirror_root,
    profile_content_roots,
    repo_notes_dirs,
)


NAVIGATION_SCHEMA_VERSION = 1
NAVIGATION_CONFIG = PurePosixPath("_meta/navigation.yml")
ROOT_NOTES = ("CLAUDE.md", "INDEX.md", "RETENTION.md", "log.md")
MAX_NOTE_BYTES = 16 * 1024 * 1024
MAX_NAVIGATION_BYTES = 256 * 1024 * 1024
MAX_NAVIGATION_DOCUMENTS = 5_000
MAX_NAVIGATION_CONFIG_BYTES = 1024 * 1024
MAX_LINKS_PER_DOCUMENT = 20_000
MAX_NAVIGATION_LINKS = 100_000
MAX_NAVIGATION_LINK_DIAGNOSTICS = 10_000

# These paths contain tooling, policy, temporary material, or repository internals.
# A configured content/mirror root is still checked against this list before use.
RESERVED_PATH_PARTS = {
    ".git",
    ".githooks",
    ".github",
    ".obsidian",
    ".vaultwright",
    "__pycache__",
    "_fixtures",
    "_meta",
    "_templates",
    "_tmp",
    "node_modules",
    "private",
    "secrets",
    "tools",
}
RESERVED_PATH_PARTS_CASEFOLD = {part.casefold() for part in RESERVED_PATH_PARTS}

# Metadata minimization is intentional.  In particular, arbitrary frontmatter is not
# copied into the model because a profile may contain private or domain-specific keys.
SAFE_FRONTMATTER_FIELDS = {
    "domain",
    "lifecycle",
    "owner",
    "related",
    "relationships",
    "repo",
    "repo_id",
    "source",
    "source_authority",
    "source_id",
    "source_path",
    "status",
    "title",
    "type",
    "updated",
}

# Wikilinks are also used as convenient local-file references in Vaultwright notes.
# These targets are outside the Markdown navigation graph and should not look like
# broken note links.  This is intentionally an allowlist so a surprising suffix is
# still diagnosed instead of silently disappearing.
NON_MARKDOWN_WIKILINK_SUFFIXES = {
    ".base",
    ".csv",
    ".doc",
    ".docx",
    ".json",
    ".pdf",
    ".ppt",
    ".pptx",
    ".toml",
    ".xls",
    ".xlsx",
    ".yaml",
    ".yml",
}

_FRONTMATTER_BOUNDARY_RE = re.compile(r"^---[ \t]*$")
_ATX_HEADING_RE = re.compile(r"^[ \t]{0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
_SETEXT_HEADING_RE = re.compile(r"^[ \t]{0,3}(=+|-+)[ \t]*$")
_FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
_WIKILINK_RE = re.compile(r"(?<!!)\[\[([^\]\n]+)\]\]")
_MARKDOWN_LINK_RE = re.compile(
    r"(?<!!)\[[^\]\n]*\]\(\s*(?:<([^>\n]+)>|([^\s)]+))"
    r"(?:\s+(?:\"[^\"\n]*\"|'[^'\n]*'))?\s*\)"
)
_INLINE_CODE_RE = re.compile(r"(`+)(.*?)\1")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_HTML_TAG_RE = re.compile(r"<[^>]*>")
_MARKDOWN_DECORATION_RE = re.compile(r"[*_~]+")


class NavigationAccessError(ValueError):
    """Raised when a document read does not satisfy the navigation boundary."""


class NavigationStaleError(NavigationAccessError):
    """Raised when a model-known document changed after the navigation scan."""


def _message_text(value: object, limit: int = 200) -> str:
    """Return a bounded, single-line representation suitable for diagnostics."""

    text = str(value).replace("\r", " ").replace("\n", " ").replace("\x00", " ")
    text = " ".join(text.split())
    if len(text) > limit:
        return text[: limit - 1] + "…"
    return text


def _sort_strings(values: Iterable[str]) -> list[str]:
    return sorted(set(values), key=lambda value: (value.casefold(), value))


def _safe_relative(value: object, *, allow_reserved: bool = False) -> PurePosixPath | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text or "\\" in text or "\x00" in text:
        return None
    path = PurePosixPath(text)
    if path.is_absolute() or not path.parts or path.as_posix() == "." or ".." in path.parts:
        return None
    if any(part in {"", "."} or part.startswith(".") for part in path.parts):
        return None
    if not allow_reserved and any(part.casefold() in RESERVED_PATH_PARTS_CASEFOLD for part in path.parts):
        return None
    return path


def _under(rel: PurePosixPath, directory: PurePosixPath) -> bool:
    return rel == directory or (
        len(rel.parts) > len(directory.parts)
        and rel.parts[: len(directory.parts)] == directory.parts
    )


def _scan_roots(root: Path) -> list[PurePosixPath]:
    configured: set[PurePosixPath] = set()
    values: list[object] = [
        *profile_content_roots(root),
        configured_office_mirror_root(root).as_posix(),
        *repo_notes_dirs(root),
    ]
    for value in values:
        rel = _safe_relative(value)
        if rel is not None:
            configured.add(rel)
    return sorted(configured, key=lambda path: (path.as_posix().casefold(), path.as_posix()))


def _is_allowed_note_path(rel: PurePosixPath, scan_roots: list[PurePosixPath]) -> bool:
    if rel.as_posix() in ROOT_NOTES:
        return True
    if rel.suffix.casefold() != ".md":
        return False
    if any(
        part.casefold() in RESERVED_PATH_PARTS_CASEFOLD or part.startswith(".")
        for part in rel.parts
    ):
        return False
    return any(_under(rel, directory) for directory in scan_roots)


def _contains_symlink(root: Path, rel: PurePosixPath) -> bool:
    current = root
    for part in rel.parts:
        current = current / part
        try:
            if current.is_symlink():
                return True
        except OSError:
            return True
    return False


def _contained_file(root: Path, rel: PurePosixPath) -> Path | None:
    if _contains_symlink(root, rel):
        return None
    candidate = root.joinpath(*rel.parts)
    try:
        resolved_root = root.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(resolved_root)
    except (FileNotFoundError, OSError, RuntimeError, ValueError):
        return None
    try:
        if not resolved.is_file():
            return None
    except OSError:
        return None
    return resolved


def _walk_markdown(root: Path, directory: PurePosixPath) -> Iterable[PurePosixPath]:
    start = root.joinpath(*directory.parts)
    if _contains_symlink(root, directory) or not start.is_dir():
        return
    for current, dirnames, filenames in os.walk(start, topdown=True, followlinks=False):
        current_path = Path(current)
        safe_dirs: list[str] = []
        for dirname in sorted(dirnames, key=lambda value: (value.casefold(), value)):
            path = current_path / dirname
            if (
                dirname.startswith(".")
                or dirname.casefold() in RESERVED_PATH_PARTS_CASEFOLD
                or path.is_symlink()
            ):
                continue
            safe_dirs.append(dirname)
        dirnames[:] = safe_dirs
        for filename in sorted(filenames, key=lambda value: (value.casefold(), value)):
            if filename.startswith(".") or not filename.casefold().endswith(".md"):
                continue
            path = current_path / filename
            if path.is_symlink():
                continue
            try:
                yield PurePosixPath(path.relative_to(root).as_posix())
            except ValueError:
                continue


def _candidate_paths(
    root: Path,
    scan_roots: list[PurePosixPath],
) -> tuple[list[PurePosixPath], bool]:
    """Return a deterministic, bounded candidate set and whether it overflowed."""

    candidates: set[PurePosixPath] = set()

    def add(rel: PurePosixPath) -> bool:
        if rel in candidates:
            return True
        if len(candidates) >= MAX_NAVIGATION_DOCUMENTS:
            return False
        candidates.add(rel)
        return True

    for filename in ROOT_NOTES:
        rel = PurePosixPath(filename)
        if (root / filename).is_file() and not (root / filename).is_symlink():
            if not add(rel):
                return (
                    sorted(candidates, key=lambda path: (path.as_posix().casefold(), path.as_posix())),
                    True,
                )
    for directory in scan_roots:
        for rel in _walk_markdown(root, directory):
            if not add(rel):
                return (
                    sorted(candidates, key=lambda path: (path.as_posix().casefold(), path.as_posix())),
                    True,
                )
    return (
        sorted(candidates, key=lambda path: (path.as_posix().casefold(), path.as_posix())),
        False,
    )


def _frontmatter(text: str) -> tuple[dict[str, Any], str, str | None]:
    """Return safe metadata, the body after frontmatter, and an optional error."""

    lines = text.splitlines(keepends=True)
    if not lines or not _FRONTMATTER_BOUNDARY_RE.match(lines[0].rstrip("\r\n")):
        return {}, text, None
    end = next(
        (
            index
            for index, line in enumerate(lines[1:], start=1)
            if _FRONTMATTER_BOUNDARY_RE.match(line.rstrip("\r\n"))
        ),
        None,
    )
    if end is None:
        return {}, text, "frontmatter opening boundary has no closing boundary"
    raw = "".join(lines[1:end])
    body = "".join(lines[end + 1 :])
    try:
        loaded = yaml.safe_load(raw) or {}
    except (yaml.YAMLError, ValueError, OverflowError, RecursionError) as exc:
        return {}, body, f"invalid YAML frontmatter ({exc.__class__.__name__})"
    if not isinstance(loaded, dict):
        return {}, body, "frontmatter must be a mapping"
    safe: dict[str, Any] = {}
    for key in sorted(SAFE_FRONTMATTER_FIELDS):
        if key not in loaded:
            continue
        value = _safe_metadata_value(loaded[key])
        if value is not None:
            safe[key] = value
    return safe, body, None


def _safe_metadata_value(value: object) -> str | list[str] | None:
    if isinstance(value, str):
        return _message_text(value, limit=1000)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, list):
        items: list[str] = []
        for item in value:
            if isinstance(item, str):
                items.append(_message_text(item, limit=1000))
            elif isinstance(item, (date, datetime)):
                items.append(item.isoformat())
            else:
                return None
        return items
    return None


def _without_fenced_code(text: str) -> str:
    out: list[str] = []
    fence_char = ""
    fence_length = 0
    for line in text.splitlines(keepends=True):
        match = _FENCE_RE.match(line)
        if match:
            marker = match.group(1)
            if not fence_char:
                fence_char = marker[0]
                fence_length = len(marker)
                out.append("\n" if line.endswith("\n") else "")
                continue
            if marker[0] == fence_char and len(marker) >= fence_length:
                fence_char = ""
                fence_length = 0
                out.append("\n" if line.endswith("\n") else "")
                continue
        if fence_char:
            out.append("\n" if line.endswith("\n") else "")
        else:
            out.append(line)
    return "".join(out)


def _plain_heading_text(value: str) -> str:
    text = value.strip()
    text = re.sub(r"!?(?:\[([^\]]+)\])\([^)]*\)", r"\1", text)
    text = re.sub(
        r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]+))?\]\]",
        lambda match: match.group(2) or match.group(1),
        text,
    )
    text = _INLINE_CODE_RE.sub(lambda match: match.group(2), text)
    text = _HTML_TAG_RE.sub("", text)
    text = _MARKDOWN_DECORATION_RE.sub("", text)
    return _message_text(" ".join(text.split()), limit=500)


def _anchor(text: str) -> str:
    value = text.casefold().strip()
    value = re.sub(r"[^\w\- ]", "", value, flags=re.UNICODE)
    return re.sub(r"[ \t]+", "-", value).strip("-")


def _headings(body: str) -> list[dict[str, Any]]:
    headings: list[dict[str, Any]] = []
    anchors: defaultdict[str, int] = defaultdict(int)

    def add(level: int, raw_text: str) -> None:
        text = _plain_heading_text(raw_text)
        if not text:
            return
        base = _anchor(text)
        if not base:
            return
        occurrence = anchors[base]
        anchors[base] += 1
        anchor = base if occurrence == 0 else f"{base}-{occurrence}"
        headings.append({"level": level, "text": text, "anchor": anchor})

    lines = _without_fenced_code(body).splitlines()
    for index, line in enumerate(lines):
        match = _ATX_HEADING_RE.match(line)
        if match:
            add(len(match.group(1)), match.group(2))
            continue
        setext = _SETEXT_HEADING_RE.match(line)
        if setext and index > 0:
            previous = lines[index - 1]
            if previous.strip() and not _ATX_HEADING_RE.match(previous):
                add(1 if setext.group(1).startswith("=") else 2, previous)
    return headings


def _title(rel: PurePosixPath, metadata: dict[str, Any], headings: list[dict[str, Any]]) -> str:
    title = metadata.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    first_h1 = next((heading["text"] for heading in headings if heading["level"] == 1), None)
    return str(first_h1 or rel.stem)


def _link_text(text: str) -> str:
    text = _without_fenced_code(text)
    text = _HTML_COMMENT_RE.sub("", text)
    return _INLINE_CODE_RE.sub("", text)


def _raw_links(text: str) -> Iterable[tuple[str, str]]:
    searchable = _link_text(text)
    for match in _WIKILINK_RE.finditer(searchable):
        target = match.group(1).split("|", 1)[0].strip()
        if target:
            yield "wikilink", target
    for match in _MARKDOWN_LINK_RE.finditer(searchable):
        target = (match.group(1) or match.group(2) or "").strip()
        if target:
            yield "markdown", target


def _normal_path(value: str) -> str:
    return PurePosixPath(value).as_posix().casefold()


def _path_indexes(paths: list[str]) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    exact: defaultdict[str, list[str]] = defaultdict(list)
    basenames: defaultdict[str, list[str]] = defaultdict(list)
    for path in paths:
        pure = PurePosixPath(path)
        exact[_normal_path(path)].append(path)
        exact[_normal_path(pure.with_suffix("").as_posix())].append(path)
        basenames[pure.stem.casefold()].append(path)
        basenames[pure.name.casefold()].append(path)
    return dict(exact), dict(basenames)


def _resolve_wikilink(
    source: str,
    raw: str,
    exact: dict[str, list[str]],
    basenames: dict[str, list[str]],
) -> tuple[list[str], str | None, bool]:
    target = unquote(raw.split("#", 1)[0]).strip()
    if not target and raw.strip().startswith("#"):
        return [source], None, True
    # Reject traversal and absolute/backslash paths before applying exclusions.  A
    # reserved-root reference is expected; a reserved-root traversal is not.
    raw_path = PurePosixPath(target) if "\\" not in target and "\x00" not in target else None
    if (
        raw_path is None
        or raw_path.is_absolute()
        or ".." in raw_path.parts
        or any(part in {"", "."} for part in raw_path.parts)
    ):
        return [], "unsafe", True
    suffix = raw_path.suffix.casefold()
    if suffix in NON_MARKDOWN_WIKILINK_SUFFIXES:
        return [], None, False
    if raw_path.parts and raw_path.parts[0].casefold() in RESERVED_PATH_PARTS_CASEFOLD:
        return [], None, False
    if target.casefold().endswith(".md"):
        target = target[:-3]
    safe = _safe_relative(target)
    if safe is None:
        return [], "unsafe", True
    candidates: set[str] = set()
    normalized = _normal_path(safe.as_posix())
    candidates.update(exact.get(normalized, []))
    if len(safe.parts) == 1:
        candidates.update(basenames.get(safe.name.casefold(), []))
    else:
        source_relative = PurePosixPath(source).parent / safe
        if ".." not in source_relative.parts:
            candidates.update(exact.get(_normal_path(source_relative.as_posix()), []))
    return _sort_strings(candidates), None, True


def _resolve_markdown_link(
    source: str,
    raw: str,
    exact: dict[str, list[str]],
) -> tuple[list[str], str | None, bool]:
    try:
        parsed = urlsplit(raw)
    except ValueError:
        return [], "unsafe", True
    if parsed.scheme or parsed.netloc:
        return [], None, False
    target = unquote(parsed.path).strip()
    if not target.casefold().endswith(".md"):
        return [], None, False
    if "\\" in target or "\x00" in target:
        return [], "unsafe", True
    if target.startswith("/"):
        combined = PurePosixPath(target.lstrip("/"))
    else:
        combined = PurePosixPath(source).parent / PurePosixPath(target)
    # Collapse '.' and '..' without ever allowing the path to escape the vault.
    parts: list[str] = []
    for part in combined.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not parts:
                return [], "unsafe", True
            parts.pop()
        else:
            parts.append(part)
    if not parts:
        return [], "unsafe", True
    rel = PurePosixPath(*parts)
    if _safe_relative(rel.as_posix()) is None:
        return [], "unsafe", True
    return _sort_strings(exact.get(_normal_path(rel.as_posix()), [])), None, True


def _build_edges(
    documents: dict[str, dict[str, Any]],
    texts: dict[str, str],
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    paths = list(documents)
    exact, basenames = _path_indexes(paths)
    pair_kinds: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    warnings: set[str] = set()
    errors: list[str] = []
    diagnostic_limit_reported = False
    global_limit_reported = False
    total_links = 0

    def warn(message: str) -> None:
        nonlocal diagnostic_limit_reported
        if message in warnings:
            return
        if len(warnings) < MAX_NAVIGATION_LINK_DIAGNOSTICS:
            warnings.add(message)
        elif not diagnostic_limit_reported:
            errors.append(
                "navigation link diagnostics exceed the 10,000-message limit; "
                "repair or narrow the collection"
            )
            diagnostic_limit_reported = True

    for source in paths:
        source_links = 0
        for kind, raw in _raw_links(texts[source]):
            if source_links >= MAX_LINKS_PER_DOCUMENT:
                errors.append(
                    f"{source}: exceeds the {MAX_LINKS_PER_DOCUMENT:,}-link Navigator note limit"
                )
                break
            if total_links >= MAX_NAVIGATION_LINKS:
                if not global_limit_reported:
                    errors.append(
                        f"navigation scan exceeds the {MAX_NAVIGATION_LINKS:,}-link total limit; "
                        "narrow the profile roots"
                    )
                    global_limit_reported = True
                break
            source_links += 1
            total_links += 1
            if kind == "wikilink":
                candidates, problem, relevant = _resolve_wikilink(
                    source,
                    raw,
                    exact,
                    basenames,
                )
            else:
                candidates, problem, relevant = _resolve_markdown_link(source, raw, exact)
            if not relevant:
                continue
            target = _message_text(raw)
            if problem == "unsafe":
                warn(f"{source}: unsafe {kind} target ignored: {target}")
            elif not candidates:
                warn(f"{source}: unresolved {kind} target: {target}")
            elif len(candidates) > 1:
                warn(
                    f"{source}: ambiguous {kind} target {target}: {', '.join(candidates)}"
                )
            else:
                pair_kinds[(source, candidates[0])].add(kind)
        if global_limit_reported:
            break
    edges = [
        {"source": source, "target": target, "kinds": _sort_strings(kinds)}
        for (source, target), kinds in sorted(
            pair_kinds.items(),
            key=lambda item: (
                item[0][0].casefold(),
                item[0][0],
                item[0][1].casefold(),
                item[0][1],
            ),
        )
    ]
    return edges, _sort_strings(warnings), errors


def _required_text(mapping: dict[str, Any], key: str, context: str, errors: list[str]) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{NAVIGATION_CONFIG.as_posix()}: {context}.{key} must be a non-empty string")
        return ""
    return _message_text(value, limit=1000)


def _audience(value: object, context: str, errors: list[str]) -> str | list[str] | None:
    if isinstance(value, str) and value.strip():
        return _message_text(value, limit=1000)
    if isinstance(value, list) and value and all(isinstance(item, str) and item.strip() for item in value):
        return [_message_text(item, limit=1000) for item in value]
    errors.append(
        f"{NAVIGATION_CONFIG.as_posix()}: {context}.audience must be a non-empty string or string list"
    )
    return None


def _resolve_trail_path(
    raw: object,
    exact: dict[str, list[str]],
    basenames: dict[str, list[str]],
) -> tuple[list[str], str | None]:
    if not isinstance(raw, str):
        return [], "unsafe"
    text = raw.strip()
    safe = _safe_relative(text)
    if safe is None:
        return [], "unsafe"
    if safe.suffix and safe.suffix.casefold() != ".md":
        return [], "unsafe"
    if not safe.suffix:
        safe = safe.with_suffix(".md")
    exact_candidates = exact.get(_normal_path(safe.as_posix()), [])
    if exact_candidates:
        return _sort_strings(exact_candidates), None
    if len(safe.parts) == 1:
        candidates = basenames.get(safe.name.casefold(), [])
    else:
        candidates = []
    return _sort_strings(candidates), None


def _load_trails(root: Path, paths: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    config_rel = NAVIGATION_CONFIG
    config_path = root.joinpath(*config_rel.parts)
    if not config_path.exists():
        return [], []
    if config_path.is_symlink() or _contains_symlink(root, config_rel):
        return [], [f"{config_rel.as_posix()}: symlinks are not allowed"]
    try:
        resolved_root = root.resolve(strict=True)
        resolved_config = config_path.resolve(strict=True)
        resolved_config.relative_to(resolved_root)
        if resolved_config.stat().st_size > MAX_NAVIGATION_CONFIG_BYTES:
            return [], [f"{config_rel.as_posix()}: exceeds the 1 MiB navigation-config limit"]
        data = yaml.safe_load(resolved_config.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return [], [f"{config_rel.as_posix()}: invalid YAML ({exc.__class__.__name__})"]
    except (OSError, RuntimeError, UnicodeError, ValueError, OverflowError) as exc:
        return [], [f"{config_rel.as_posix()}: cannot read ({exc.__class__.__name__})"]
    if not isinstance(data, dict):
        return [], [f"{config_rel.as_posix()}: must be a mapping"]
    errors: list[str] = []
    schema_version = data.get("schema_version")
    if (
        not isinstance(schema_version, int)
        or isinstance(schema_version, bool)
        or schema_version != NAVIGATION_SCHEMA_VERSION
    ):
        errors.append(f"{config_rel.as_posix()}: schema_version must be {NAVIGATION_SCHEMA_VERSION}")
        return [], errors
    raw_trails = data.get("trails", [])
    if not isinstance(raw_trails, list):
        errors.append(f"{config_rel.as_posix()}: trails must be a list")
        return [], errors
    exact, basenames = _path_indexes(paths)
    trails: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw_trail in enumerate(raw_trails):
        context = f"trails[{index}]"
        start_error_count = len(errors)
        if not isinstance(raw_trail, dict):
            errors.append(f"{config_rel.as_posix()}: {context} must be a mapping")
            continue
        trail_id = _required_text(raw_trail, "id", context, errors)
        title = _required_text(raw_trail, "title", context, errors)
        goal = _required_text(raw_trail, "goal", context, errors)
        audience = _audience(raw_trail.get("audience"), context, errors)
        if trail_id and trail_id in seen_ids:
            errors.append(f"{config_rel.as_posix()}: duplicate trail id: {trail_id}")
        steps_raw = raw_trail.get("steps")
        steps: list[dict[str, str]] = []
        if not isinstance(steps_raw, list) or not steps_raw:
            errors.append(f"{config_rel.as_posix()}: {context}.steps must be a non-empty list")
        else:
            for step_index, raw_step in enumerate(steps_raw):
                step_context = f"{context}.steps[{step_index}]"
                if not isinstance(raw_step, dict):
                    errors.append(f"{config_rel.as_posix()}: {step_context} must be a mapping")
                    continue
                why = _required_text(raw_step, "why", step_context, errors)
                raw_path = raw_step.get("path")
                candidates, problem = _resolve_trail_path(raw_path, exact, basenames)
                path_label = _message_text(raw_path)
                if problem == "unsafe":
                    errors.append(
                        f"{config_rel.as_posix()}: {step_context}.path is unsafe: {path_label}"
                    )
                elif not candidates:
                    errors.append(
                        f"{config_rel.as_posix()}: {step_context}.path is missing: {path_label}"
                    )
                elif len(candidates) > 1:
                    errors.append(
                        f"{config_rel.as_posix()}: {step_context}.path is ambiguous: "
                        f"{path_label} ({', '.join(candidates)})"
                    )
                elif why:
                    steps.append({"path": candidates[0], "node_id": candidates[0], "why": why})
        if len(errors) == start_error_count and audience is not None:
            seen_ids.add(trail_id)
            trails.append(
                {
                    "id": trail_id,
                    "title": title,
                    "goal": goal,
                    "audience": audience,
                    "steps": steps,
                }
            )
    return trails, errors


def _read_note(root: Path, rel: PurePosixPath) -> tuple[dict[str, Any], str] | None:
    path = _contained_file(root, rel)
    if path is None:
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    metadata, body, frontmatter_error = _frontmatter(text)
    headings = _headings(body)
    link_parts = [] if frontmatter_error == "frontmatter opening boundary has no closing boundary" else [body]
    for field in ("related", "relationships"):
        value = metadata.get(field)
        if isinstance(value, str):
            link_parts.append(value)
        elif isinstance(value, list):
            link_parts.extend(item for item in value if isinstance(item, str))
    node = {
        "id": rel.as_posix(),
        "path": rel.as_posix(),
        "title": _title(rel, metadata, headings),
        "revision": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "frontmatter": metadata,
        "headings": headings,
        "outbound": [],
        "inbound": [],
    }
    if frontmatter_error:
        node["_frontmatter_error"] = frontmatter_error
    return node, "\n".join(link_parts)


def build_navigation_model(root: Path | str) -> tuple[dict[str, Any], list[str], list[str]]:
    """Build a stable metadata-only navigation model for ``root``.

    Notes are limited to profile-declared content roots, configured mirror roots,
    configured repository-note roots, and Vaultwright's four root documents.  Link
    problems are warnings.  Authored trail schema/path problems are errors.
    """

    vault = Path(root)
    warnings: list[str] = []
    errors: list[str] = []
    try:
        vault = vault.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        return (
            {"schema_version": NAVIGATION_SCHEMA_VERSION, "nodes": [], "edges": [], "trails": []},
            [],
            [f"vault root cannot be read ({exc.__class__.__name__})"],
        )
    if not vault.is_dir():
        return (
            {"schema_version": NAVIGATION_SCHEMA_VERSION, "nodes": [], "edges": [], "trails": []},
            [],
            ["vault root must be a directory"],
        )

    scan_roots = _scan_roots(vault)
    documents: dict[str, dict[str, Any]] = {}
    texts: dict[str, str] = {}
    total_bytes = 0
    candidate_paths, candidate_limit_exceeded = _candidate_paths(vault, scan_roots)
    if candidate_limit_exceeded:
        errors.append(
            f"navigation document limit exceeded ({MAX_NAVIGATION_DOCUMENTS}); narrow the profile roots"
        )
    for rel in candidate_paths:
        if not _is_allowed_note_path(rel, scan_roots):
            continue
        candidate = _contained_file(vault, rel)
        if candidate is None:
            warnings.append(f"{rel.as_posix()}: unreadable Markdown note skipped")
            continue
        try:
            note_bytes = candidate.stat().st_size
        except OSError:
            warnings.append(f"{rel.as_posix()}: unreadable Markdown note skipped")
            continue
        if note_bytes > MAX_NOTE_BYTES:
            errors.append(f"{rel.as_posix()}: exceeds the 16 MiB Navigator note limit")
            continue
        if total_bytes + note_bytes > MAX_NAVIGATION_BYTES:
            errors.append(
                "navigation scan exceeds the 256 MiB total limit; narrow the profile roots"
            )
            break
        loaded = _read_note(vault, rel)
        if loaded is None:
            warnings.append(f"{rel.as_posix()}: unreadable Markdown note skipped")
            continue
        total_bytes += note_bytes
        node, text = loaded
        frontmatter_error = node.pop("_frontmatter_error", None)
        if frontmatter_error:
            warnings.append(f"{rel.as_posix()}: {frontmatter_error}")
        documents[rel.as_posix()] = node
        texts[rel.as_posix()] = text

    edges, link_warnings, link_errors = _build_edges(documents, texts)
    warnings.extend(link_warnings)
    errors.extend(link_errors)
    outbound: defaultdict[str, set[str]] = defaultdict(set)
    inbound: defaultdict[str, set[str]] = defaultdict(set)
    for edge in edges:
        outbound[edge["source"]].add(edge["target"])
        inbound[edge["target"]].add(edge["source"])
    for path, node in documents.items():
        node["outbound"] = _sort_strings(outbound[path])
        node["inbound"] = _sort_strings(inbound[path])

    paths = list(documents)
    trails, trail_errors = _load_trails(vault, paths)
    errors.extend(trail_errors)
    model = {
        "schema_version": NAVIGATION_SCHEMA_VERSION,
        "nodes": [documents[path] for path in paths],
        "edges": edges,
        "trails": trails,
    }
    return model, _sort_strings(warnings), _sort_strings(errors)


def _model_paths(model: object) -> set[str]:
    if not isinstance(model, dict) or not isinstance(model.get("nodes"), list):
        return set()
    paths: set[str] = set()
    for node in model["nodes"]:
        if not isinstance(node, dict):
            continue
        path = node.get("path")
        if isinstance(path, str):
            paths.add(path)
    return paths


def _model_node(model: object, path: str) -> dict[str, Any] | None:
    if not isinstance(model, dict) or not isinstance(model.get("nodes"), list):
        return None
    return next(
        (
            node
            for node in model["nodes"]
            if isinstance(node, dict) and node.get("path") == path
        ),
        None,
    )


def read_document(
    root: Path | str,
    path: str,
    model: dict[str, Any],
) -> dict[str, Any]:
    """Read one model-known Markdown note after rechecking filesystem safety."""

    if not isinstance(path, str):
        raise NavigationAccessError("document path must be a string")
    rel = _safe_relative(path)
    # Root notes are safe exceptions to the generic relative-path rule.
    if path in ROOT_NOTES:
        rel = PurePosixPath(path)
    if rel is None or rel.suffix.casefold() != ".md":
        raise NavigationAccessError("document path is unsafe")
    model_node = _model_node(model, rel.as_posix())
    if model_node is None:
        raise NavigationAccessError("document path is not present in the navigation model")
    vault = Path(root)
    try:
        vault = vault.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise NavigationAccessError("vault root cannot be read") from exc
    scan_roots = _scan_roots(vault)
    if not _is_allowed_note_path(rel, scan_roots):
        raise NavigationAccessError("document path is outside navigation roots")
    resolved = _contained_file(vault, rel)
    if resolved is None:
        raise NavigationAccessError("document path is missing, linked, or outside the vault")
    try:
        if resolved.stat().st_size > MAX_NOTE_BYTES:
            raise NavigationAccessError("document exceeds the 16 MiB Navigator note limit")
        text = resolved.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise NavigationAccessError("document cannot be read as UTF-8 Markdown") from exc
    revision = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if model_node.get("revision") != revision:
        raise NavigationStaleError("document changed after the navigation scan; rescan required")
    metadata, body, _frontmatter_error = _frontmatter(text)
    headings = _headings(body)
    return {
        "path": rel.as_posix(),
        "title": _title(rel, metadata, headings),
        "frontmatter": metadata,
        "headings": headings,
        "content_type": "text/markdown",
        "revision": revision,
        "content": text,
    }
