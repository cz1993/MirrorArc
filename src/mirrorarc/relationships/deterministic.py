# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build deterministic relationship state from manifests, profiles, and classified Markdown."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

from mirrorarc.knowledge_inventory import build_inventory, stable_projection_id
from mirrorarc.relationships.model import EvidenceAnchor, stable_id
from mirrorarc.relationships.store import RelationshipStore
from mirrorarc.runtime_profile import load_profile_mapping


def _load_records(root: Path, rel: str) -> list[dict[str, Any]]:
    path = root / rel
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    records = value.get("records", []) if isinstance(value, dict) else []
    return [dict(record) for record in records if isinstance(record, dict)] if isinstance(records, list) else []


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _domain_for(path: str, domain_folders: dict[str, str]) -> str:
    parts = Path(path).parts
    if not parts:
        return ""
    for domain, folder in domain_folders.items():
        if parts[0] == folder:
            return domain
    return ""


def _frontmatter(path: Path) -> dict[str, Any]:
    if yaml is None or not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    try:
        value = yaml.safe_load(text[3:end].lstrip("\n")) or {}
    except yaml.YAMLError:
        return {}
    return value if isinstance(value, dict) else {}


def _artifact(
    artifact_id: str,
    *,
    kind: str,
    layer: str,
    path: str = "",
    title: str = "",
    domain: str = "",
    content_hash: str = "",
    lifecycle: str = "current",
    authority: str = "derived",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "artifact_kind": kind,
        "layer": layer,
        "path": path,
        "title": title or (Path(path).stem if path else artifact_id),
        "domain": domain,
        "content_hash": content_hash,
        "lifecycle_state": lifecycle,
        "authority": authority,
        "metadata": metadata or {},
    }


def graph_plan(root: Path) -> dict[str, Any]:
    root = root.expanduser().resolve()
    profile = load_profile_mapping(root)
    profile_id = str(profile.get("id", "unknown") or "unknown") if isinstance(profile, dict) else "unknown"
    profile_version = str(profile.get("profile_version", "") or "") if isinstance(profile, dict) else ""
    raw_domains = profile.get("domains", {}) if isinstance(profile, dict) else {}
    domain_folders = {
        str(domain): str(value.get("folder"))
        for domain, value in raw_domains.items()
        if isinstance(value, dict) and value.get("folder")
    } if isinstance(raw_domains, dict) else {}
    inventory = build_inventory(root)
    artifacts: dict[str, dict[str, Any]] = {}
    relationships: list[dict[str, Any]] = []

    profile_artifact_id = f"profile:{profile_id}@{profile_version}"
    artifacts[profile_artifact_id] = _artifact(
        profile_artifact_id, kind="profile", layer="control", title=profile_id,
        authority="operational", metadata={"profile_version": profile_version},
    )

    def ensure_target(kind: str, value: str) -> str:
        artifact_id = f"{kind}:{value}"
        if artifact_id not in artifacts:
            artifacts[artifact_id] = _artifact(
                artifact_id, kind=kind, layer="control", title=value, authority="operational"
            )
        return artifact_id

    def add_relation(
        source: str,
        target: str,
        rel_type: str,
        *,
        source_hash: str = "",
        target_hash: str = "",
        selector: str,
    ) -> None:
        relationships.append({
            "source_artifact_id": source,
            "target_artifact_id": target,
            "relationship_type": rel_type,
            "method": "deterministic",
            "method_version": "knowledge-projection:v1",
            "state": "accepted",
            "source_hash": source_hash,
            "target_hash": target_hash,
            "evidence": [EvidenceAnchor(
                artifact_id=source,
                selector_type="metadata",
                selector_value=selector,
                source_hash=source_hash,
            )],
        })

    def attach_governance(artifact_id: str, *, domain: str, lifecycle: str, content_hash: str, selector: str) -> None:
        if domain:
            add_relation(
                artifact_id, ensure_target("domain", domain), "IN_DOMAIN",
                source_hash=content_hash, selector=selector,
            )
        add_relation(
            artifact_id, profile_artifact_id, "IN_PROFILE", source_hash=content_hash, selector=selector,
        )
        add_relation(
            artifact_id, ensure_target("lifecycle", lifecycle or "current"), "HAS_LIFECYCLE",
            source_hash=content_hash, selector=selector,
        )

    for record in _load_records(root, "_meta/source-manifest.json"):
        source_id = str(record.get("source_id", "") or "").strip()
        if not source_id:
            continue
        source_path = str(record.get("current_source_path", "") or "")
        domain = _domain_for(source_path, domain_folders)
        source_hash = str(record.get("source_sha256", "") or "")
        lifecycle = str(record.get("lifecycle_state", "clean") or "clean")
        artifacts[source_id] = _artifact(
            source_id, kind="source", layer="L0", path=source_path, domain=domain,
            content_hash=source_hash, lifecycle=lifecycle, authority="authoritative",
            metadata={"source_format": record.get("source_format", ""), "manifest": "source"},
        )
        attach_governance(source_id, domain=domain, lifecycle=lifecycle, content_hash=source_hash, selector="source-manifest")
        projection_id = str(record.get("projection_id", "") or stable_projection_id(source_id))
        projection_path = str(record.get("mirror_path", "") or "")
        projection_hash = str(record.get("generated_region_sha256", "") or "")
        artifacts[projection_id] = _artifact(
            projection_id, kind="projection", layer="L1", path=projection_path, domain=domain,
            content_hash=projection_hash, lifecycle=lifecycle, authority="derived",
            metadata={"source_id": source_id, "manifest": "source"},
        )
        attach_governance(projection_id, domain=domain, lifecycle=lifecycle, content_hash=projection_hash, selector="source-manifest")
        add_relation(projection_id, source_id, "MIRRORS", source_hash=projection_hash, target_hash=source_hash, selector="source-manifest")
        add_relation(projection_id, source_id, "DERIVED_FROM", source_hash=projection_hash, target_hash=source_hash, selector="source-manifest")

    for record in _load_records(root, "_meta/repo-manifest.json"):
        repo_id = str(record.get("repo_id", "") or "").strip()
        if not repo_id:
            continue
        source_path = str(record.get("source_ref", record.get("configured_repo", "")) or "")
        projection_path = str(record.get("note_path", "") or "")
        domain = _domain_for(projection_path, domain_folders)
        source_hash = str(record.get("last_commit", "") or "")
        lifecycle = str(record.get("lifecycle_state", "clean") or "clean")
        artifacts[repo_id] = _artifact(
            repo_id, kind="repository", layer="L0", path=source_path, domain=domain,
            content_hash=source_hash, lifecycle=lifecycle, authority="authoritative",
            metadata={"source_type": record.get("source_type", "github"), "manifest": "repository"},
        )
        attach_governance(repo_id, domain=domain, lifecycle=lifecycle, content_hash=source_hash, selector="repo-manifest")
        projection_id = str(record.get("projection_id", "") or stable_projection_id(repo_id))
        projection_hash = str(record.get("generated_region_sha256", "") or "")
        artifacts[projection_id] = _artifact(
            projection_id, kind="projection", layer="L1", path=projection_path, domain=domain,
            content_hash=projection_hash, lifecycle=lifecycle, authority="derived",
            metadata={"source_id": repo_id, "manifest": "repository"},
        )
        attach_governance(projection_id, domain=domain, lifecycle=lifecycle, content_hash=projection_hash, selector="repo-manifest")
        add_relation(projection_id, repo_id, "MIRRORS", source_hash=projection_hash, target_hash=source_hash, selector="repo-manifest")
        add_relation(projection_id, repo_id, "DERIVED_FROM", source_hash=projection_hash, target_hash=source_hash, selector="repo-manifest")

    for item in inventory["native_sources"]:
        path = str(item["path"])
        artifact_id = str(item["source_id"])
        actual = root / path
        content_hash = _file_hash(actual) if actual.is_file() else ""
        domain = _domain_for(path, domain_folders)
        artifacts[artifact_id] = _artifact(
            artifact_id, kind="native-source", layer="L0", path=path, domain=domain,
            content_hash=content_hash, lifecycle="current", authority="authoritative",
            metadata={"source_format": item["format"], "projection_policy": item["projection_policy"]},
        )
        attach_governance(artifact_id, domain=domain, lifecycle="current", content_hash=content_hash, selector="native-registration")

    for item in inventory["markdown"]["items"]:
        category = str(item.get("category", ""))
        path = str(item.get("path", ""))
        if category not in {"index", "operational_control", "l2_generated_view", "l2_reviewed_view"}:
            continue
        # The append-only run log is operational audit evidence, not a knowledge dependency.
        # Including its wall-clock entries would make an otherwise identical source rebuild
        # produce a different deterministic graph fingerprint on every materialization.
        if path == "log.md":
            continue
        actual = root / path
        fm = _frontmatter(actual)
        if category.startswith("l2_"):
            artifact_id = str(fm.get("view_id", "") or stable_id("view", path))
            layer, kind, authority = "L2", "knowledge-view", "reviewed" if category == "l2_reviewed_view" else "derived"
            lifecycle = str(fm.get("view_state", fm.get("status", "generated")) or "generated")
        else:
            artifact_id = stable_id("control", path)
            layer, kind, authority, lifecycle = "control", category, "operational", "current"
        if artifact_id in artifacts:
            continue
        content_hash = str(item.get("sha256", "") or "")
        domain = str(fm.get("domain", "") or _domain_for(path, domain_folders))
        artifacts[artifact_id] = _artifact(
            artifact_id, kind=kind, layer=layer, path=path, title=str(fm.get("title", "") or ""),
            domain=domain, content_hash=content_hash, lifecycle=lifecycle, authority=authority,
            metadata={"markdown_category": category},
        )
        attach_governance(artifact_id, domain=domain, lifecycle=lifecycle, content_hash=content_hash, selector="markdown-inventory")

    return {
        "schema_version": 1,
        "profile_id": profile_id,
        "artifacts": [artifacts[key] for key in sorted(artifacts)],
        "relationships": sorted(
            relationships,
            key=lambda item: (
                item["source_artifact_id"], item["relationship_type"], item["target_artifact_id"]
            ),
        ),
        "inventory_errors": list(inventory["errors"]),
    }


def refresh(root: Path) -> dict[str, Any]:
    # Preserve the old ledger hashes long enough to invalidate dependent views before
    # replacing the graph with the current source manifest.
    from mirrorarc.relationships.invalidation import reconcile_derived_state
    reconcile_derived_state(root)
    plan = graph_plan(root)
    store = RelationshipStore(root)
    result = store.replace_deterministic(plan["artifacts"], plan["relationships"])
    # Governed L2 files and frozen context packs intentionally survive local database loss. Reattach
    # them after the baseline graph replacement so their dependency edges are not dropped by a full
    # deterministic refresh.
    from mirrorarc.context_assembly.builder import reconcile_persisted_contexts
    from mirrorarc.knowledge_views.store import KnowledgeViewStore

    view_recovery = KnowledgeViewStore(root).reconcile_persisted()
    context_recovery = reconcile_persisted_contexts(root)
    from mirrorarc.document_intelligence.service import reconcile_indexes
    document_recovery = reconcile_indexes(root)
    return {
        **result,
        "fingerprint": store.deterministic_fingerprint(),
        "profile_id": plan["profile_id"],
        "inventory_errors": plan["inventory_errors"],
        "reattached": {"views": view_recovery, "contexts": context_recovery, "documents": document_recovery},
    }


def refresh_source_record(root: Path, record: dict[str, Any]) -> dict[str, Any]:
    """Refresh one Office source/L1 subgraph without reading unrelated source bodies."""
    root = root.expanduser().resolve()
    source_id = str(record.get("source_id", "") or "").strip()
    if not source_id:
        return {"artifacts": 0, "relationships": 0, "source_id": ""}
    projection_id = str(record.get("projection_id", "") or stable_projection_id(source_id))
    profile = load_profile_mapping(root)
    profile_id = str(profile.get("id", "unknown") or "unknown") if isinstance(profile, dict) else "unknown"
    profile_version = str(profile.get("profile_version", "") or "") if isinstance(profile, dict) else ""
    raw_domains = profile.get("domains", {}) if isinstance(profile, dict) else {}
    domain_folders = {
        str(domain): str(value.get("folder"))
        for domain, value in raw_domains.items()
        if isinstance(value, dict) and value.get("folder")
    } if isinstance(raw_domains, dict) else {}
    source_path = str(record.get("current_source_path", "") or "")
    projection_path = str(record.get("mirror_path", "") or "")
    domain = _domain_for(source_path, domain_folders)
    source_hash = str(record.get("source_sha256", "") or "")
    projection_hash = str(record.get("generated_region_sha256", "") or "")
    lifecycle = str(record.get("lifecycle_state", "clean") or "clean")
    profile_artifact_id = f"profile:{profile_id}@{profile_version}"
    domain_id = f"domain:{domain}" if domain else ""
    lifecycle_id = f"lifecycle:{lifecycle}"
    artifacts = [
        _artifact(
            source_id, kind="source", layer="L0", path=source_path, domain=domain,
            content_hash=source_hash, lifecycle=lifecycle, authority="authoritative",
            metadata={"source_format": record.get("source_format", ""), "manifest": "source"},
        ),
        _artifact(
            projection_id, kind="projection", layer="L1", path=projection_path, domain=domain,
            content_hash=projection_hash, lifecycle=lifecycle, authority="derived",
            metadata={"source_id": source_id, "manifest": "source"},
        ),
        _artifact(profile_artifact_id, kind="profile", layer="control", title=profile_id, authority="operational"),
        _artifact(lifecycle_id, kind="lifecycle", layer="control", title=lifecycle, authority="operational"),
    ]
    if domain_id:
        artifacts.append(_artifact(domain_id, kind="domain", layer="control", title=domain, authority="operational"))
    relationships: list[dict[str, Any]] = []

    def add(source: str, target: str, rel_type: str, source_value: str, target_value: str, selector: str) -> None:
        relationships.append({
            "source_artifact_id": source, "target_artifact_id": target,
            "relationship_type": rel_type, "method": "deterministic",
            "method_version": "knowledge-projection:v1", "state": "accepted",
            "source_hash": source_value, "target_hash": target_value,
            "evidence": [EvidenceAnchor(source, "metadata", selector, source_value)],
        })

    for artifact_id, content_hash in ((source_id, source_hash), (projection_id, projection_hash)):
        if domain_id:
            add(artifact_id, domain_id, "IN_DOMAIN", content_hash, "", "source-manifest")
        add(artifact_id, profile_artifact_id, "IN_PROFILE", content_hash, "", "source-manifest")
        add(artifact_id, lifecycle_id, "HAS_LIFECYCLE", content_hash, "", "source-manifest")
    add(projection_id, source_id, "MIRRORS", projection_hash, source_hash, "source-manifest")
    add(projection_id, source_id, "DERIVED_FROM", projection_hash, source_hash, "source-manifest")
    result = RelationshipStore(root).replace_deterministic_for_artifacts(
        {source_id, projection_id}, artifacts, relationships
    )
    return {**result, "source_id": source_id, "projection_id": projection_id}
