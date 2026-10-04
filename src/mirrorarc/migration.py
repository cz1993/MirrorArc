#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Report legacy folders/frontmatter domains and optionally normalize known frontmatter aliases."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Missing dependency: pip install pyyaml")

from mirrorarc.profiles import ProfileValidationError, load_profile
from mirrorarc.runtime_profile import (
    configured_office_mirror_root,
    load_profile_mapping,
    profile_machine_owned_note_types,
)


DEFAULT_ROOT = Path.cwd()
PROFILE_REL = Path("_meta/profile.yml")
DOMAIN_MAP_REL = Path("_meta/domain-map.yml")
SOURCE_EXTS = {".docx", ".pptx", ".xlsx", ".doc", ".pdf"}
STRUCTURAL_MD = {"AGENTS.md", "CLAUDE.md", "INDEX.md", "RETENTION.md", "CATALOG.md", "log.md"}
GENERATED_SENTINEL = "%% AUTO-GENERATED BELOW"
RESERVED_TOP_LEVEL = {
    ".git",
    ".githooks",
    ".github",
    ".obsidian",
    "_archive",
    "_fixtures",
    "_meta",
    "_mirrors",
    "_templates",
    "_tmp",
    "node_modules",
    "tools",
}
PROFILE_DOMAIN_PREVIEW_LIMIT = 12
MARKDOWN_CATEGORIES = {
    "index",
    "authoritative_markdown_source",
    "l1_projection",
    "l2_generated_view",
    "l2_reviewed_view",
    "operational_control",
    "legacy_curated_derivative",
    "unknown",
}
TARGET_MARKDOWN_CATEGORIES = MARKDOWN_CATEGORIES - {"legacy_curated_derivative", "unknown"}
OPERATIONAL_MARKDOWN_NAMES = {
    "AGENTS.md",
    "CLAUDE.md",
    "RETENTION.md",
    "CATALOG.md",
    "log.md",
}
OPERATIONAL_MARKDOWN_ROOTS = {"_meta", "_templates", "tools"}
SOURCE_MANIFEST_REL = Path("_meta/source-manifest.json")
REPO_MANIFEST_REL = Path("_meta/repo-manifest.json")


def active_profile_summary(root: Path) -> dict[str, object]:
    profile = load_profile_mapping(root)
    if not profile:
        return {
            "id": "",
            "name": "",
            "profile_version": "",
            "domains": [],
        }
    domains: list[dict[str, str]] = []
    raw_domains = profile.get("domains")
    if isinstance(raw_domains, dict):
        for domain, definition in sorted(raw_domains.items(), key=lambda item: str(item[0])):
            if not isinstance(definition, dict):
                continue
            folder = definition.get("folder")
            if not isinstance(folder, str) or not folder.strip():
                continue
            domains.append({"id": str(domain), "folder": folder.strip()})
    return {
        "id": str(profile.get("id", "") or ""),
        "name": str(profile.get("name", "") or ""),
        "profile_version": str(profile.get("profile_version", "") or ""),
        "domains": domains,
    }


def active_profile_label(summary: dict[str, object]) -> str:
    profile_id = str(summary.get("id", "") or "")
    version = str(summary.get("profile_version", "") or "")
    if profile_id and version:
        return f"{profile_id} {version}"
    if profile_id:
        return profile_id
    return "unavailable or legacy profile"


def profile_domain_preview(summary: dict[str, object]) -> str:
    domains = summary.get("domains")
    if not isinstance(domains, list) or not domains:
        return "none declared"
    entries: list[str] = []
    for item in domains[:PROFILE_DOMAIN_PREVIEW_LIMIT]:
        if not isinstance(item, dict):
            continue
        domain_id = str(item.get("id", "") or "")
        folder = str(item.get("folder", "") or "")
        if domain_id and folder:
            entries.append(f"{domain_id} -> {folder}")
    remaining = len(domains) - len(entries)
    if remaining > 0:
        entries.append(f"... {remaining} more")
    return ", ".join(entries) if entries else "none declared"


def print_active_profile_context(root: Path) -> None:
    summary = active_profile_summary(root)
    print("## Active Profile")
    print()
    print(f"- Profile: `{md_escape(active_profile_label(summary))}`")
    print(f"- Canonical domain folders: `{md_escape(profile_domain_preview(summary))}`")
    print("- `_meta/profile.yml` is authoritative for canonical domains and folders.")
    print("- `_meta/domain-map.yml` is only the legacy alias and operator-guidance layer.")
    print()


def load_profile_routing(
    root: Path,
) -> tuple[dict[str, str], dict[str, dict[str, str]], set[str], list[str]]:
    path = root / PROFILE_REL
    if not path.exists():
        return {}, {}, set(), [f"{PROFILE_REL.as_posix()}: missing"]
    try:
        profile = load_profile(path)
    except ProfileValidationError as exc:
        message = str(exc).replace(str(path), PROFILE_REL.as_posix())
        return {}, {}, set(), [f"{PROFILE_REL.as_posix()}: invalid profile contract ({message})"]

    canonical: dict[str, str] = {}
    aliases: dict[str, dict[str, str]] = {}
    canonical_domains: set[str] = set()
    errors: list[str] = []
    for domain, info in profile.domains.items():
        if not isinstance(info, dict) or not info.get("folder"):
            errors.append(f"{PROFILE_REL.as_posix()}:domains.{domain}: missing folder")
            continue
        domain_name = str(domain)
        folder = str(info["folder"])
        canonical_domains.add(domain_name)
        canonical[folder] = domain_name
        for key in (domain_name, folder):
            aliases[key] = {"domain": domain_name, "folder": folder}
    if not canonical:
        errors.append(f"{PROFILE_REL.as_posix()}: no valid domains")
    return canonical, aliases, canonical_domains, errors


def load_domain_routing(
    root: Path,
) -> tuple[dict[str, str], dict[str, dict[str, str]], set[str], list[str], list[str]]:
    canonical, aliases, canonical_domains, profile_errors = load_profile_routing(root)
    if profile_errors:
        return canonical, aliases, canonical_domains, [], profile_errors

    path = root / DOMAIN_MAP_REL
    if not path.exists():
        return (
            canonical,
            aliases,
            canonical_domains,
            [f"{DOMAIN_MAP_REL.as_posix()}: missing; legacy aliases unavailable"],
            [],
        )
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return canonical, aliases, canonical_domains, [], [
            f"{DOMAIN_MAP_REL.as_posix()}: invalid YAML ({exc.__class__.__name__})"
        ]
    domains = data.get("domains")
    if not isinstance(domains, dict) or not domains:
        return canonical, aliases, canonical_domains, [], [f"{DOMAIN_MAP_REL.as_posix()}: missing domains map"]

    errors: list[str] = []
    profile_folders = {domain: folder for folder, domain in canonical.items()}
    for domain, info in domains.items():
        if not isinstance(info, dict) or not info.get("folder"):
            errors.append(f"{DOMAIN_MAP_REL.as_posix()}:{domain}: missing folder")
            continue
        domain_name = str(domain)
        folder = str(info["folder"])
        expected_folder = profile_folders.get(domain_name, "")
        if domain_name not in canonical_domains:
            errors.append(f"{DOMAIN_MAP_REL.as_posix()}:{domain_name}: domain not declared in {PROFILE_REL.as_posix()}")
            continue
        if expected_folder and expected_folder != folder:
            errors.append(f"{DOMAIN_MAP_REL.as_posix()}:{domain_name}: folder differs from {PROFILE_REL.as_posix()}")
            folder = expected_folder
        for key in (domain_name, folder):
            aliases[key] = {"domain": domain_name, "folder": folder}
        raw_aliases = info.get("aliases", [])
        if isinstance(raw_aliases, list):
            for alias in raw_aliases:
                if isinstance(alias, str) and alias.strip():
                    aliases[alias.strip()] = {"domain": domain_name, "folder": folder}
    return canonical, aliases, canonical_domains, [], errors


def folder_counts(path: Path) -> dict[str, int]:
    counts = {"files": 0, "dirs": 0, "markdown": 0, "office": 0}
    for child in path.rglob("*"):
        if child.is_symlink():
            continue
        if child.is_dir():
            counts["dirs"] += 1
            continue
        if not child.is_file():
            continue
        counts["files"] += 1
        suffix = child.suffix.lower()
        if suffix == ".md":
            counts["markdown"] += 1
        if suffix in SOURCE_EXTS:
            counts["office"] += 1
    return counts


def should_ignore_top_level(path: Path, canonical_folders: set[str]) -> bool:
    name = path.name
    return name in RESERVED_TOP_LEVEL or name in canonical_folders


def excluded_rel(rel: Path) -> bool:
    return any(part in RESERVED_TOP_LEVEL or part.startswith(".") for part in rel.parts)


def split_frontmatter(text: str) -> tuple[dict | None, str]:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            try:
                data = yaml.safe_load(text[3:end].lstrip("\n")) or {}
            except yaml.YAMLError:
                return None, text
            return data if isinstance(data, dict) else None, text[end + 4:]
    return {}, text


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_json_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(raw, list):
        records = raw
    elif isinstance(raw, dict):
        records = raw.get("records", raw.get("sources", raw.get("repos", [])))
    else:
        return []
    return [record for record in records if isinstance(record, dict)] if isinstance(records, list) else []


def manifest_owned_markdown(root: Path) -> set[str]:
    owned: set[str] = set()
    for rel, keys in (
        (SOURCE_MANIFEST_REL, ("mirror_path", "projection_path")),
        (REPO_MANIFEST_REL, ("note_path", "mirror_path")),
    ):
        for record in load_json_records(root / rel):
            for key in keys:
                value = record.get(key)
                if isinstance(value, str) and value.strip().endswith(".md"):
                    candidate = Path(value.strip())
                    if not candidate.is_absolute() and ".." not in candidate.parts:
                        owned.add(candidate.as_posix())
    return owned


def profile_note_type_roles(root: Path) -> dict[str, dict]:
    path = root / PROFILE_REL
    if not path.exists():
        return {}
    try:
        profile = load_profile(path)
    except ProfileValidationError:
        return {}
    return {
        str(note_type): dict(definition)
        for note_type, definition in profile.note_types.items()
        if isinstance(definition, dict)
    }


def recommended_disposition(category: str) -> str:
    return {
        "index": "keep_manual_guide",
        "authoritative_markdown_source": "register_as_source",
        "l1_projection": "regenerate_from_source",
        "l2_generated_view": "regenerate_or_leave_ephemeral",
        "l2_reviewed_view": "preserve_review_and_dependencies",
        "operational_control": "keep_operational_control",
        "legacy_curated_derivative": "review_for_lens_promotion_archive_or_removal",
        "unknown": "classify_before_write",
    }[category]


def classify_markdown(
    root: Path,
    path: Path,
    *,
    manifest_owned: set[str],
    note_type_roles: dict[str, dict],
    mirror_root: Path,
) -> dict:
    rel = path.relative_to(root)
    rel_text = rel.as_posix()
    text = path.read_text(encoding="utf-8", errors="replace")
    frontmatter, body = split_frontmatter(text)
    frontmatter = frontmatter if isinstance(frontmatter, dict) else None
    declared = str((frontmatter or {}).get("markdown_category", "") or "")
    note_type = str((frontmatter or {}).get("type", "") or "")
    view_state = str((frontmatter or {}).get("view_state", (frontmatter or {}).get("status", "")) or "")
    classification_rule = ""

    if rel_text == "INDEX.md":
        category = "index"
        classification_rule = "index_path"
    elif rel_text in manifest_owned:
        category = "l1_projection"
        classification_rule = "manifest_owned"
    elif declared in TARGET_MARKDOWN_CATEGORIES:
        category = declared
        classification_rule = "declared_frontmatter"
    elif rel.parts and (rel.parts[0] in OPERATIONAL_MARKDOWN_ROOTS or path.name in OPERATIONAL_MARKDOWN_NAMES):
        category = "operational_control"
        classification_rule = "operational_path"
    elif rel.parts and rel.parts[0] == "_fixtures":
        category = "authoritative_markdown_source"
        classification_rule = "declared_source_fixture"
    elif rel.parts and mirror_root.parts and rel.parts[: len(mirror_root.parts)] == mirror_root.parts:
        category = "l1_projection" if GENERATED_SENTINEL in body else "unknown"
        classification_rule = "mirror_root_sentinel" if category == "l1_projection" else "unmanaged_mirror_root"
    elif note_type in note_type_roles and note_type_roles[note_type].get("legacy_derivative") is True:
        category = "legacy_curated_derivative"
        classification_rule = "profile_legacy_note_type"
    elif note_type in note_type_roles:
        role = note_type_roles[note_type]
        role_category = str(role.get("markdown_category", "") or "")
        if role_category in TARGET_MARKDOWN_CATEGORIES:
            category = role_category
            classification_rule = "profile_note_type"
        elif role.get("machine_owned") is True:
            category = "l1_projection"
            classification_rule = "profile_machine_owned_note_type"
        elif note_type == "knowledge-view":
            category = "l2_reviewed_view" if view_state in {"reviewed", "stale", "superseded"} else "l2_generated_view"
            classification_rule = "knowledge_view_state"
        else:
            category = "authoritative_markdown_source"
            classification_rule = "declared_profile_note_type"
    elif frontmatter is None:
        category = "unknown"
        classification_rule = "invalid_frontmatter"
    else:
        category = "unknown"
        classification_rule = "no_allowed_category_evidence"

    return {
        "path": rel_text,
        "sha256": sha256_text(text),
        "category": category,
        "classification_rule": classification_rule,
        "declared_category": declared,
        "note_type": note_type,
        "view_state": view_state,
        "recommended_disposition": recommended_disposition(category),
    }


def markdown_inventory(root: Path) -> list[dict]:
    root = root.expanduser().resolve()
    manifest_owned = manifest_owned_markdown(root)
    note_type_roles = profile_note_type_roles(root)
    mirror_root = configured_office_mirror_root(root)
    items: list[dict] = []
    for path in sorted(root.rglob("*.md"), key=lambda candidate: candidate.relative_to(root).as_posix()):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(root)
        if any(part in {".git", ".mirrorarc", ".vaultwright", "node_modules"} for part in rel.parts):
            continue
        items.append(
            classify_markdown(
                root,
                path,
                manifest_owned=manifest_owned,
                note_type_roles=note_type_roles,
                mirror_root=mirror_root,
            )
        )
    return items


def markdown_summary(items: list[dict]) -> dict[str, int]:
    counts = {category: 0 for category in sorted(MARKDOWN_CATEGORIES)}
    for item in items:
        category = str(item.get("category", "unknown"))
        counts[category if category in counts else "unknown"] += 1
    return {"total": len(items), **counts, "unexplained": counts["unknown"]}


def _is_within(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
    except ValueError:
        return False
    return True


def load_markdown_review(path: Path) -> dict:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"cannot read review manifest: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"review manifest is not valid JSON: {exc}") from exc
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise ValueError("review manifest must be a schema_version 1 object")
    if raw.get("reviewed") is not True or not isinstance(raw.get("reviewer"), str) or not raw["reviewer"].strip():
        raise ValueError("review manifest requires reviewed=true and a non-empty reviewer")
    if not isinstance(raw.get("items"), list):
        raise ValueError("review manifest items must be a list")
    return raw


def apply_markdown_review(
    root: Path,
    review_path: Path,
    backup_dir: Path,
    *,
    write: bool,
) -> dict:
    root = root.expanduser().resolve()
    review = load_markdown_review(review_path.expanduser().resolve())
    backup_dir = backup_dir.expanduser().resolve()
    if backup_dir == root or _is_within(backup_dir, root):
        raise ValueError("backup directory must be outside the vault")

    results: list[dict] = []
    seen: set[str] = set()
    for index, raw_item in enumerate(review["items"]):
        if not isinstance(raw_item, dict):
            raise ValueError(f"review manifest item {index} must be an object")
        rel_text = str(raw_item.get("path", "") or "")
        rel = Path(rel_text)
        if not rel_text or rel.is_absolute() or ".." in rel.parts or rel.suffix.lower() != ".md":
            raise ValueError(f"review manifest item {index} has an unsafe Markdown path")
        if rel.as_posix() in seen:
            raise ValueError(f"review manifest path is duplicated: {rel.as_posix()}")
        seen.add(rel.as_posix())
        action = str(raw_item.get("action", "") or "")
        category = str(raw_item.get("category", "") or "")
        if action != "set_category" or category not in TARGET_MARKDOWN_CATEGORIES:
            raise ValueError(f"review manifest item {index} must use set_category with an allowed target category")
        path = root / rel
        if not path.is_file() or path.is_symlink():
            results.append({"path": rel.as_posix(), "status": "error", "reason": "missing or symlink"})
            continue
        text = path.read_text(encoding="utf-8")
        frontmatter, body = split_frontmatter(text)
        if not isinstance(frontmatter, dict) or not frontmatter:
            results.append({"path": rel.as_posix(), "status": "error", "reason": "valid frontmatter required"})
            continue
        if str(frontmatter.get("markdown_category", "") or "") == category:
            results.append({"path": rel.as_posix(), "status": "unchanged", "category": category})
            continue
        expected = str(raw_item.get("expected_sha256", "") or "")
        if len(expected) != 64 or expected != sha256_text(text):
            results.append({"path": rel.as_posix(), "status": "error", "reason": "hash changed since review"})
            continue
        if category == "authoritative_markdown_source" and str(frontmatter.get("type", "")) == "knowledge-view":
            provenance = raw_item.get("promotion_provenance")
            if not isinstance(provenance, dict) or not provenance.get("source_view_id"):
                results.append({"path": rel.as_posix(), "status": "error", "reason": "promotion provenance required"})
                continue

        if not write:
            results.append({"path": rel.as_posix(), "status": "planned", "category": category})
            continue
        backup_path = backup_dir / rel
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        if backup_path.exists() and backup_path.read_bytes() != path.read_bytes():
            results.append({"path": rel.as_posix(), "status": "error", "reason": "backup target already differs"})
            continue
        if not backup_path.exists():
            shutil.copy2(path, backup_path)
        updated = dict(frontmatter)
        updated["markdown_category"] = category
        if category == "authoritative_markdown_source" and raw_item.get("promotion_provenance"):
            updated["promotion_provenance"] = raw_item["promotion_provenance"]
        write_text_atomic(path, dump_frontmatter(updated) + body)
        results.append({"path": rel.as_posix(), "status": "updated", "category": category})

    errors = sum(1 for item in results if item["status"] == "error")
    return {
        "reviewer": review["reviewer"].strip(),
        "review_manifest": str(review_path.expanduser().resolve()),
        "backup_dir": str(backup_dir),
        "write": write,
        "summary": {
            "total": len(results),
            "planned": sum(1 for item in results if item["status"] == "planned"),
            "updated": sum(1 for item in results if item["status"] == "updated"),
            "unchanged": sum(1 for item in results if item["status"] == "unchanged"),
            "errors": errors,
        },
        "items": results,
    }


def print_markdown_inventory_worksheet(items: list[dict]) -> None:
    summary = markdown_summary(items)
    print("## Markdown Inventory")
    print()
    print(f"- Total Markdown files: {summary['total']}")
    print(f"- Unexplained Markdown files: {summary['unexplained']}")
    for category in sorted(MARKDOWN_CATEGORIES):
        print(f"- `{category}`: {summary[category]}")
    print()
    print("## Markdown Disposition Review")
    print()
    for item in items:
        print(
            f"- [ ] `{md_escape(item['path'])}` — `{md_escape(item['category'])}` "
            f"via `{md_escape(item['classification_rule'])}`"
        )
        print(f"  - SHA-256: `{item['sha256']}`")
        print(f"  - Recommended disposition: `{item['recommended_disposition']}`")
    print()


def dump_frontmatter(frontmatter: dict) -> str:
    dumped = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True)
    return f"---\n{dumped}---"


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with tmp.open("w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def frontmatter_domain_items(root: Path, aliases: dict[str, dict[str, str]], canonical_domains: set[str]) -> list[dict]:
    items: list[dict] = []
    machine_owned_note_types = profile_machine_owned_note_types(root)
    for path in sorted(root.rglob("*.md"), key=lambda p: p.relative_to(root).as_posix()):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(root)
        if excluded_rel(rel) or path.name in STRUCTURAL_MD:
            continue
        fm, _body = split_frontmatter(path.read_text(encoding="utf-8", errors="ignore"))
        if not isinstance(fm, dict):
            continue
        if str(fm.get("type", "") or "") in machine_owned_note_types:
            continue
        raw_domain = fm.get("domain")
        if raw_domain in (None, ""):
            continue
        current_domain = str(raw_domain)
        if current_domain in canonical_domains:
            continue
        alias = aliases.get(current_domain)
        if alias:
            kind = "frontmatter_domain_alias"
            recommended_domain = alias["domain"]
            recommended_folder = alias["folder"]
            action = (
                f"Review, then update frontmatter `domain: {recommended_domain}` and move the note "
                f"under {recommended_folder}/ if ownership belongs there."
            )
        else:
            kind = "frontmatter_domain_unknown"
            recommended_domain = ""
            recommended_folder = ""
            action = (
                "Review whether the domain maps to an active profile domain in _meta/profile.yml "
                "or requires a profile contract change; use _meta/domain-map.yml only for legacy "
                "aliases after the canonical domain is chosen."
            )
        items.append({
            "kind": kind,
            "path": rel.as_posix(),
            "note_type": str(fm.get("type", "")),
            "current_domain": current_domain,
            "recommended_domain": recommended_domain,
            "recommended_folder": recommended_folder,
            "current_folder": rel.parts[0] if rel.parts else "",
            "action": action,
        })
    return items


def build_report(root: Path) -> tuple[list[dict], list[dict], list[str], list[str]]:
    canonical, aliases, canonical_domains, routing_warnings, errors = load_domain_routing(root)
    if errors:
        return [], [], routing_warnings, errors

    items: list[dict] = []
    warnings: list[str] = list(routing_warnings)
    canonical_folders = set(canonical)
    for path in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not path.is_dir() or path.is_symlink():
            continue
        if should_ignore_top_level(path, canonical_folders):
            continue
        alias = aliases.get(path.name)
        counts = folder_counts(path)
        if path.name.startswith((".", "_")):
            warnings.append(f"{path.name}: non-reserved hidden/underscore folder reported for review")
        if alias and alias["folder"] != path.name:
            items.append({
                "kind": "alias_folder",
                "folder": path.name,
                "domain": alias["domain"],
                "recommended_folder": alias["folder"],
                "counts": counts,
                "action": (
                    f"Review, then move contents into {alias['folder']}/; update links/frontmatter; "
                    "remove the old folder only after backup review."
                ),
            })
        else:
            items.append({
                "kind": "unknown_folder",
                "folder": path.name,
                "domain": "",
                "recommended_folder": "",
                "counts": counts,
                "action": (
                    "Review whether this belongs under an active profile folder from "
                    "_meta/profile.yml or requires a profile contract change; use "
                    "_meta/domain-map.yml only for legacy aliases after the canonical folder is chosen."
                ),
            })
    return items, frontmatter_domain_items(root, aliases, canonical_domains), warnings, []


def summary_counts(items: list[dict]) -> dict[str, int]:
    return {
        "total": len(items),
        "alias": sum(1 for item in items if item["kind"] == "alias_folder"),
        "unknown": sum(1 for item in items if item["kind"] == "unknown_folder"),
    }


def frontmatter_summary_counts(items: list[dict]) -> dict[str, int]:
    return {
        "total": len(items),
        "alias": sum(1 for item in items if item["kind"] == "frontmatter_domain_alias"),
        "unknown": sum(1 for item in items if item["kind"] == "frontmatter_domain_unknown"),
    }


def md_escape(value: object) -> str:
    return str(value).replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def print_worksheet(
    root: Path,
    items: list[dict],
    frontmatter_items: list[dict],
    markdown_items: list[dict],
    warnings: list[str],
    errors: list[str],
) -> None:
    summary = summary_counts(items)
    frontmatter_summary = frontmatter_summary_counts(frontmatter_items)
    print("# MirrorArc Migration Review Worksheet")
    print()
    print("Generated by `mirrorarc migration --worksheet`. Dry-run only; no files were moved.")
    print()
    print("## Summary")
    print()
    print(f"- Vault root: `{md_escape(root)}`")
    print(
        "- Top-level folders needing review: "
        f"{summary['total']} (alias={summary['alias']}, unknown={summary['unknown']})"
    )
    print(
        "- Note frontmatter domains needing review: "
        f"{frontmatter_summary['total']} "
        f"(alias={frontmatter_summary['alias']}, unknown={frontmatter_summary['unknown']})"
    )
    print()
    if warnings or errors:
        print("## Preflight Notes")
        print()
        for warning in warnings:
            print(f"- Warning: {md_escape(warning)}")
        for error in errors:
            print(f"- Error: {md_escape(error)}")
        print()
    print_active_profile_context(root)
    print("## Review Protocol")
    print()
    print("- Confirm the copied vault is backed up before moving files.")
    print("- Move one folder or note group at a time, then update frontmatter and links.")
    print("- Run `mirrorarc migration`, `mirrorarc catalog`, and `mirrorarc lint` after each batch.")
    print("- Archive or remove legacy folders only after source ownership and links are reviewed.")
    print()
    print("## Top-Level Folder Review")
    print()
    if not items:
        print("- [ ] No legacy or unknown top-level folders found.")
    for item in items:
        target = item["recommended_folder"] or "manual classification"
        counts = item["counts"]
        details = (
            f"files={counts['files']}, dirs={counts['dirs']}, "
            f"markdown={counts['markdown']}, office={counts['office']}"
        )
        print(f"- [ ] `{md_escape(item['folder'])}` -> `{md_escape(target)}` ({md_escape(item['kind'])}; {details})")
        if item["domain"]:
            print(f"  - Domain: `{md_escape(item['domain'])}`")
        print(f"  - Action: {md_escape(item['action'])}")
    print()
    print("## Frontmatter Domain Review")
    print()
    if not frontmatter_items:
        print("- [ ] No legacy frontmatter domains found.")
    for item in frontmatter_items:
        target = item["recommended_domain"] or "manual classification"
        print(
            f"- [ ] `{md_escape(item['path'])}`: "
            f"`{md_escape(item['current_domain'])}` -> `{md_escape(target)}` "
            f"({md_escape(item['kind'])})"
        )
        if item["recommended_folder"]:
            print(f"  - Recommended folder: `{md_escape(item['recommended_folder'])}`")
        print(f"  - Action: {md_escape(item['action'])}")
    print()
    print_markdown_inventory_worksheet(markdown_items)


def print_runbook(root: Path, items: list[dict], frontmatter_items: list[dict], warnings: list[str], errors: list[str]) -> None:
    summary = summary_counts(items)
    frontmatter_summary = frontmatter_summary_counts(frontmatter_items)
    print("# MirrorArc Legacy Folder Migration Runbook")
    print()
    print("Generated by `mirrorarc migration --runbook`. Read-only; no files were moved or changed.")
    print()
    print("## Current Queue")
    print()
    print(f"- Vault root: `{md_escape(root)}`")
    print(
        "- Top-level folders needing review: "
        f"{summary['total']} (alias={summary['alias']}, unknown={summary['unknown']})"
    )
    print(
        "- Frontmatter domains needing review: "
        f"{frontmatter_summary['total']} "
        f"(alias={frontmatter_summary['alias']}, unknown={frontmatter_summary['unknown']})"
    )
    print()
    if warnings or errors:
        print("## Preflight Notes")
        print()
        for warning in warnings:
            print(f"- Warning: {md_escape(warning)}")
        for error in errors:
            print(f"- Error: {md_escape(error)}")
        print()
    print_active_profile_context(root)
    print("## Preconditions")
    print()
    mirror_root = configured_office_mirror_root(root).as_posix()
    print("- Work only in a permission-cleared copied vault, never the original source collection.")
    print(f"- Confirm `{mirror_root}/` is the generated mirror root before moving source folders.")
    print("- Confirm the copied vault is backed up or committed before each migration batch.")
    print("- Resolve `mirrorarc recovery --worksheet` items before trusting generated mirrors.")
    print("- Treat unknown folders/domains as classification decisions, not automatic moves.")
    print()
    print("## Execution Sequence")
    print()
    print("1. Run `mirrorarc migration --worksheet` and review the folder/domain queue.")
    print("2. Run `mirrorarc migration --normalize-frontmatter-domains --worksheet`.")
    print("3. If approved, run `mirrorarc migration --normalize-frontmatter-domains --write`.")
    print(
        "4. Classify unknown folders/domains against `_meta/profile.yml`; record legacy aliases in "
        "`_meta/domain-map.yml` or a private decision log only after the canonical profile domain is chosen."
    )
    print("5. Move one alias folder batch at a time into the recommended canonical folder.")
    print("6. Update affected wikilinks, note frontmatter, hub links, and entity pages.")
    print("7. Regenerate `mirrorarc catalog` and `mirrorarc catalog --html`.")
    print("8. Run `mirrorarc migration`, `mirrorarc recovery --worksheet`, and `mirrorarc lint`.")
    print("9. Archive or remove legacy folders only after links, catalog, and lint are clean.")
    print()
    print("## Folder Move Rules")
    print()
    print("- Prefer manual review or `git mv` over broad shell moves.")
    print(f"- Move authoritative source records only after review; do not move generated L1 projections out of `{mirror_root}/`.")
    print("- Preserve mixed-content folders as subfolders until ownership is clear.")
    print("- Do not merge unrelated profile domains only because paths match; use the active profile domain list above.")
    print("- Keep old folders until the post-move verification checklist passes.")
    print()
    print("## Stop Conditions")
    print()
    print("- Stop if `mirrorarc recovery --worksheet` reports missing sources, conflicts, or manual generated edits.")
    print("- Stop if `mirrorarc lint` reports broken links, invalid domains, or stale mirrors.")
    print("- Stop if a folder mixes multiple active-profile domains and cannot be classified confidently.")
    print("- Stop if source ownership, retention posture, or privacy sensitivity is unclear.")
    print()
    print("## Alias Folder Queue")
    print()
    alias_items = [item for item in items if item["kind"] == "alias_folder"]
    if not alias_items:
        print("- [ ] No legacy alias folders found.")
    for item in alias_items:
        counts = item["counts"]
        print(
            f"- [ ] `{md_escape(item['folder'])}/` -> `{md_escape(item['recommended_folder'])}/` "
            f"(domain=`{md_escape(item['domain'])}`, files={counts['files']}, markdown={counts['markdown']}, office={counts['office']})"
        )
    print()
    print("## Unknown Classification Queue")
    print()
    unknown_items = [item for item in items if item["kind"] == "unknown_folder"]
    unknown_frontmatter = [item for item in frontmatter_items if item["kind"] == "frontmatter_domain_unknown"]
    if not unknown_items and not unknown_frontmatter:
        print("- [ ] No unknown folders or frontmatter domains found.")
    for item in unknown_items:
        counts = item["counts"]
        print(
            f"- [ ] Folder `{md_escape(item['folder'])}/`: classify before moving "
            f"(files={counts['files']}, markdown={counts['markdown']}, office={counts['office']})"
        )
    for item in unknown_frontmatter:
        print(
            f"- [ ] Note `{md_escape(item['path'])}`: classify domain "
            f"`{md_escape(item['current_domain'])}` before changing frontmatter."
        )
    print()
    print("## Post-Migration Evidence")
    print()
    print("- Save the completed private worksheet/runbook outside this public repository.")
    print("- Record commands run, reviewer, decision date, and remaining exceptions.")
    print("- Keep only aggregate pilot evidence in this repository; never commit source content or private paths.")
    print()


def print_human(
    root: Path,
    items: list[dict],
    frontmatter_items: list[dict],
    markdown_items: list[dict],
    warnings: list[str],
    errors: list[str],
) -> None:
    print(f"mirrorarc migration: {root}")
    print("migration: dry-run only; no files were moved")
    for warning in warnings:
        print(f"  warning: {warning}")
    for error in errors:
        print(f"  error: {error}", file=sys.stderr)
    if errors:
        return
    summary = summary_counts(items)
    if not items:
        print("migration: no legacy or unknown top-level folders found")
    else:
        print(
            "migration: "
            f"{summary['total']} top-level folders need review "
            f"(alias={summary['alias']}, unknown={summary['unknown']})"
        )
        for item in items:
            target = item["recommended_folder"] or "manual classification"
            print(f"  [{item['kind']:<14}] {item['folder']} -> {target}")
            if item["domain"]:
                print(f"    domain: {item['domain']}")
            counts = item["counts"]
            print(
                "    contents: "
                f"files={counts['files']}, dirs={counts['dirs']}, "
                f"markdown={counts['markdown']}, office={counts['office']}"
            )
            print(f"    action: {item['action']}")

    frontmatter_summary = frontmatter_summary_counts(frontmatter_items)
    if not frontmatter_items:
        print("migration: no legacy frontmatter domains found")
    else:
        print(
            "migration: "
            f"{frontmatter_summary['total']} note frontmatter domains need review "
            f"(alias={frontmatter_summary['alias']}, unknown={frontmatter_summary['unknown']})"
        )
        for item in frontmatter_items:
            target = item["recommended_domain"] or "manual classification"
            print(f"  [{item['kind']}] {item['path']}: {item['current_domain']} -> {target}")
            if item["recommended_folder"]:
                print(f"    folder: {item['recommended_folder']}")
            print(f"    action: {item['action']}")
    md_summary = markdown_summary(markdown_items)
    print(
        "migration: Markdown inventory "
        f"total={md_summary['total']}, legacy={md_summary['legacy_curated_derivative']}, "
        f"unknown={md_summary['unknown']}"
    )


def normalize_frontmatter_domain_aliases(
    root: Path,
    frontmatter_items: list[dict],
    *,
    write: bool,
) -> tuple[list[dict], list[str]]:
    results: list[dict] = []
    errors: list[str] = []
    machine_owned_note_types = profile_machine_owned_note_types(root)
    for item in frontmatter_items:
        if item.get("kind") != "frontmatter_domain_alias":
            continue
        rel = Path(str(item.get("path", "")))
        if rel.is_absolute() or ".." in rel.parts:
            results.append({"status": "skipped", **item, "reason": "unsafe path"})
            continue
        path = root / rel
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            results.append({"status": "skipped", **item, "reason": f"unreadable ({exc.__class__.__name__})"})
            continue
        fm, body = split_frontmatter(text)
        if not isinstance(fm, dict) or not fm:
            results.append({"status": "skipped", **item, "reason": "missing or invalid frontmatter"})
            continue
        if str(fm.get("type", "") or "") in machine_owned_note_types or GENERATED_SENTINEL in body:
            results.append({"status": "skipped", **item, "reason": "generated mirror"})
            continue
        current_domain = str(fm.get("domain", ""))
        expected_current = str(item.get("current_domain", ""))
        recommended_domain = str(item.get("recommended_domain", ""))
        if not recommended_domain:
            results.append({"status": "skipped", **item, "reason": "no canonical recommendation"})
            continue
        if current_domain != expected_current:
            results.append({"status": "skipped", **item, "reason": "domain changed since report"})
            continue
        updated_fm = dict(fm)
        updated_fm["domain"] = recommended_domain
        if write:
            try:
                write_text_atomic(path, dump_frontmatter(updated_fm) + body)
            except OSError as exc:
                errors.append(f"{rel.as_posix()}: write failed ({exc.__class__.__name__})")
                results.append({"status": "error", **item, "reason": f"write failed ({exc.__class__.__name__})"})
                continue
            status = "updated"
        else:
            status = "planned"
        results.append({"status": status, **item})
    return results, errors


def print_normalize_frontmatter_domains(
    root: Path,
    frontmatter_items: list[dict],
    warnings: list[str],
    errors: list[str],
    *,
    write: bool,
) -> int:
    mode = "write mode; no files were moved" if write else "dry-run only; use --write to update files"
    print(f"mirrorarc migration normalize-frontmatter-domains: {root}")
    print(f"migration normalize-frontmatter-domains: {mode}")
    for warning in warnings:
        print(f"  warning: {warning}")
    for error in errors:
        print(f"  error: {error}", file=sys.stderr)
    if errors:
        return 1

    results, write_errors = normalize_frontmatter_domain_aliases(root, frontmatter_items, write=write)
    unknown_count = sum(1 for item in frontmatter_items if item.get("kind") == "frontmatter_domain_unknown")
    status_counts = {
        "planned": sum(1 for item in results if item["status"] == "planned"),
        "updated": sum(1 for item in results if item["status"] == "updated"),
        "skipped": sum(1 for item in results if item["status"] == "skipped"),
        "error": sum(1 for item in results if item["status"] == "error"),
    }
    eligible = sum(1 for item in frontmatter_items if item.get("kind") == "frontmatter_domain_alias")
    print(
        "migration normalize-frontmatter-domains: "
        f"{eligible} alias domain(s) eligible, "
        f"planned={status_counts['planned']}, updated={status_counts['updated']}, "
        f"skipped={status_counts['skipped']}, errors={status_counts['error']}, unknown={unknown_count}"
    )
    if unknown_count:
        print("migration normalize-frontmatter-domains: unknown domains were not changed")
    for item in results:
        target = item.get("recommended_domain") or "manual classification"
        print(f"  [{item['status']:<7}] {item['path']}: {item['current_domain']} -> {target}")
        if item.get("reason"):
            print(f"    reason: {item['reason']}")
    for error in write_errors:
        print(f"  error: {error}", file=sys.stderr)
    return 1 if write_errors else 0


def print_normalize_frontmatter_domains_worksheet(
    root: Path,
    frontmatter_items: list[dict],
    warnings: list[str],
    errors: list[str],
) -> int:
    print("# MirrorArc Frontmatter Domain Normalization Worksheet")
    print()
    print(
        "Generated by `mirrorarc migration --normalize-frontmatter-domains --worksheet`. "
        "Dry-run only; no files were changed."
    )
    print()
    for error in errors:
        print(f"- Error: {md_escape(error)}")
    if errors:
        return 1

    results, read_errors = normalize_frontmatter_domain_aliases(root, frontmatter_items, write=False)
    unknown_items = [item for item in frontmatter_items if item.get("kind") == "frontmatter_domain_unknown"]
    status_counts = {
        "planned": sum(1 for item in results if item["status"] == "planned"),
        "skipped": sum(1 for item in results if item["status"] == "skipped"),
        "error": sum(1 for item in results if item["status"] == "error"),
    }
    eligible = sum(1 for item in frontmatter_items if item.get("kind") == "frontmatter_domain_alias")

    print("## Summary")
    print()
    print(f"- Vault root: `{md_escape(root)}`")
    print(f"- Alias domains eligible for known canonical rewrite: {eligible}")
    print(f"- Planned frontmatter updates: {status_counts['planned']}")
    print(f"- Skipped alias notes: {status_counts['skipped']}")
    print(f"- Unknown domains needing manual classification: {len(unknown_items)}")
    print(f"- Errors: {status_counts['error'] + len(read_errors)}")
    print()
    if warnings or read_errors:
        print("## Preflight Notes")
        print()
        for warning in warnings:
            print(f"- Warning: {md_escape(warning)}")
        for error in read_errors:
            print(f"- Error: {md_escape(error)}")
        print()
    print_active_profile_context(root)

    print("## Review Protocol")
    print()
    print("- Confirm the copied vault is backed up before applying any writes.")
    print("- Review every planned frontmatter change below; this worksheet does not move files.")
    print("- Treat skipped generated mirrors as source/repo-sync artifacts, not hand-edited notes.")
    print("- Classify unknown domains against `_meta/profile.yml`; use `_meta/domain-map.yml` only for legacy aliases.")
    print("- After approval, run `mirrorarc migration --normalize-frontmatter-domains --write`.")
    print("- Then regenerate `mirrorarc catalog` and run `mirrorarc lint`.")
    print()

    print("## Planned Frontmatter Updates")
    print()
    planned = [item for item in results if item["status"] == "planned"]
    if not planned:
        print("- [ ] No known alias frontmatter updates found.")
    for item in planned:
        print(
            f"- [ ] `{md_escape(item['path'])}`: "
            f"`{md_escape(item['current_domain'])}` -> `{md_escape(item['recommended_domain'])}`"
        )
        if item.get("recommended_folder"):
            print(f"  - Recommended folder: `{md_escape(item['recommended_folder'])}`")
    print()

    print("## Skipped Alias Notes")
    print()
    skipped = [item for item in results if item["status"] == "skipped"]
    if not skipped:
        print("- [ ] No known alias notes were skipped.")
    for item in skipped:
        print(
            f"- [ ] `{md_escape(item['path'])}`: "
            f"`{md_escape(item['current_domain'])}` -> `{md_escape(item['recommended_domain'])}`"
        )
        print(f"  - Reason: {md_escape(item.get('reason', 'skipped'))}")
    print()

    print("## Unknown Domain Review")
    print()
    if not unknown_items:
        print("- [ ] No unknown frontmatter domains found.")
    for item in unknown_items:
        print(
            f"- [ ] `{md_escape(item['path'])}`: "
            f"`{md_escape(item['current_domain'])}` -> `manual classification`"
        )
        print(f"  - Action: {md_escape(item['action'])}")
    print()
    return 1 if read_errors or status_counts["error"] else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Report MirrorArc folder/frontmatter migration work.")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="Print machine-readable migration JSON.")
    output.add_argument("--worksheet", action="store_true", help="Print a Markdown migration review worksheet.")
    output.add_argument("--runbook", action="store_true", help="Print a Markdown legacy-folder migration runbook.")
    parser.add_argument(
        "--normalize-frontmatter-domains",
        action="store_true",
        help="Preview known legacy frontmatter domain aliases that can be rewritten to canonical domains.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="With --normalize-frontmatter-domains, rewrite known frontmatter domain aliases. Does not move files.",
    )
    parser.add_argument(
        "--apply-markdown-review",
        type=Path,
        help="Apply a reviewed, hash-pinned Markdown classification manifest.",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        help="Backup directory outside the vault, required with --apply-markdown-review.",
    )
    return parser


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    active_root = (root or DEFAULT_ROOT).expanduser().resolve()
    if args.write and not (args.normalize_frontmatter_domains or args.apply_markdown_review):
        parser.error("--write requires --normalize-frontmatter-domains or --apply-markdown-review")
    if args.normalize_frontmatter_domains and args.apply_markdown_review:
        parser.error("--normalize-frontmatter-domains and --apply-markdown-review are mutually exclusive")
    if args.apply_markdown_review and not args.backup_dir:
        parser.error("--apply-markdown-review requires --backup-dir")
    if args.backup_dir and not args.apply_markdown_review:
        parser.error("--backup-dir requires --apply-markdown-review")
    if args.normalize_frontmatter_domains and (args.json or args.runbook):
        parser.error("--normalize-frontmatter-domains cannot be combined with --json or --runbook")
    if args.normalize_frontmatter_domains and args.write and args.worksheet:
        parser.error("--write cannot be combined with --worksheet")
    items, frontmatter_items, warnings, errors = build_report(active_root)
    markdown_items = markdown_inventory(active_root)
    if args.apply_markdown_review:
        try:
            result = apply_markdown_review(
                active_root,
                args.apply_markdown_review,
                args.backup_dir,
                write=args.write,
            )
        except ValueError as exc:
            print(f"migration markdown review: {exc}", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            mode = "applied" if args.write else "planned"
            print(f"migration markdown review: {mode}; reviewer={result['reviewer']}")
            print(json.dumps(result["summary"], sort_keys=True))
        return 1 if result["summary"]["errors"] else 0
    if args.normalize_frontmatter_domains:
        if args.worksheet:
            return print_normalize_frontmatter_domains_worksheet(
                active_root,
                frontmatter_items,
                warnings,
                errors,
            )
        return print_normalize_frontmatter_domains(
            active_root,
            frontmatter_items,
            warnings,
            errors,
            write=args.write,
        )
    if args.json:
        print(json.dumps({
            "root": str(active_root),
            "summary": summary_counts(items),
            "frontmatter_summary": frontmatter_summary_counts(frontmatter_items),
            "markdown_summary": markdown_summary(markdown_items),
            "items": items,
            "frontmatter_items": frontmatter_items,
            "markdown_items": markdown_items,
            "warnings": warnings,
            "errors": errors,
        }, indent=2, sort_keys=True))
    elif args.worksheet:
        print_worksheet(active_root, items, frontmatter_items, markdown_items, warnings, errors)
    elif args.runbook:
        print_runbook(active_root, items, frontmatter_items, warnings, errors)
    else:
        print_human(active_root, items, frontmatter_items, markdown_items, warnings, errors)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
