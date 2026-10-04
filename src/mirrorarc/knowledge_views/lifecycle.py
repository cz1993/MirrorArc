# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit L2 persistence, review, and promotion operations."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

import yaml

from mirrorarc.knowledge_views.store import KnowledgeViewError, KnowledgeViewStore
from mirrorarc.relationships.model import EvidenceAnchor
from mirrorarc.relationships.store import RelationshipStore, utc_now

PERSISTED_ROOT = Path("_meta/knowledge-views")


def _read_output(root: Path, record: dict[str, Any]) -> str:
    rel = Path(str(record["output_path"]))
    if rel.is_absolute() or ".." in rel.parts:
        raise KnowledgeViewError("view output path is unsafe")
    path = root / rel
    if not path.is_file() or path.is_symlink():
        raise KnowledgeViewError("view output is missing or unsafe")
    text = path.read_text(encoding="utf-8")
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != record["output_hash"]:
        raise KnowledgeViewError("view output hash differs from recorded generation")
    return text


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(text, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:].lstrip()
    return text


def _persisted_document(record: dict[str, Any], body: str, *, reviewed: bool, reviewer: str = "") -> str:
    state = "reviewed" if reviewed else "generated"
    frontmatter = {
        "title": str(record["lens_id"]).replace("-", " ").title(),
        "type": "knowledge-view",
        "status": "active" if reviewed else "draft",
        "markdown_category": "l2_reviewed_view" if reviewed else "l2_generated_view",
        "authority": "reviewed-derived" if reviewed else "derived",
        "view_id": record["view_id"],
        "lens_id": record["lens_id"],
        "view_state": state,
        "version": record["version"],
        "definition_hash": record["definition_hash"],
        "dependency_hash": record["dependency_hash"],
        "output_hash": record["output_hash"],
        "generation_method": record["generation_method"],
        "model_version": record.get("model_version", ""),
        "prompt_version": record.get("prompt_version", ""),
        "citations": record.get("citations", []),
        "reviewer": reviewer,
        "reviewed_at": utc_now() if reviewed else "",
    }
    return "---\n" + yaml.safe_dump(frontmatter,sort_keys=False,allow_unicode=True) + "---\n\n" + body.lstrip()


def pin_view(root: Path, view_id: str) -> dict[str, Any]:
    root = root.expanduser().resolve()
    store = KnowledgeViewStore(root)
    record = store.get(view_id)
    if record is None:
        raise KnowledgeViewError(f"unknown view_id: {view_id}")
    body = _read_output(root, record)
    rel = PERSISTED_ROOT / "pinned" / f"{view_id}.md"
    document = _persisted_document(record, _strip_frontmatter(body), reviewed=False)
    _write_atomic(root / rel, document)
    return store.set_pinned(view_id, rel.as_posix(), hashlib.sha256(document.encode("utf-8")).hexdigest())


def review_view(root: Path, view_id: str, *, reviewer: str) -> dict[str, Any]:
    root = root.expanduser().resolve()
    store = KnowledgeViewStore(root)
    record = store.get(view_id)
    if record is None:
        raise KnowledgeViewError(f"unknown view_id: {view_id}")
    body = _read_output(root, record)
    rel = PERSISTED_ROOT / "reviewed" / f"{view_id}.md"
    document = _persisted_document(record, _strip_frontmatter(body), reviewed=True, reviewer=reviewer)
    persisted_hash = hashlib.sha256(document.encode("utf-8")).hexdigest()
    _write_atomic(root / rel, document)
    reviewed = store.review(view_id, reviewer, rel.as_posix(), persisted_hash)
    RelationshipStore(root).upsert_artifact({
        "artifact_id":view_id,"artifact_kind":"knowledge-view","layer":"L2","path":rel.as_posix(),
        "title":record["lens_id"],"content_hash":persisted_hash,"lifecycle_state":"reviewed",
        "authority":"reviewed-derived","metadata":{"lens_id":record["lens_id"],"dependency_hash":record["dependency_hash"],"version":record["version"]},
    })
    return reviewed


def promote_view(root: Path, view_id: str, *, target: Path, reviewer: str, reason: str) -> dict[str, Any]:
    root = root.expanduser().resolve()
    store = KnowledgeViewStore(root)
    record = store.get(view_id)
    if record is None or record["state"] != "reviewed":
        raise KnowledgeViewError("only a reviewed view can be promoted")
    reviewer_value, reason_value = reviewer.strip(), reason.strip()
    if not reviewer_value or not reason_value:
        raise KnowledgeViewError("promotion requires reviewer and reason")
    target_path = target if target.is_absolute() else root / target
    target_path = target_path.resolve()
    if not target_path.is_relative_to(root) or target_path.suffix.lower() != ".md":
        raise KnowledgeViewError("promotion target must be a Markdown path inside the vault")
    if target_path.exists():
        raise KnowledgeViewError("promotion target already exists")
    body = _strip_frontmatter(_read_output(root, record))
    profile_path = root / "_meta" / "profile.yml"
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) if profile_path.exists() else {}
    relative_target = target_path.relative_to(root)
    domain = ""
    for domain_id, definition in (profile.get("domains", {}) if isinstance(profile, dict) else {}).items():
        if isinstance(definition, dict) and relative_target.parts and definition.get("folder") == relative_target.parts[0]:
            domain = str(domain_id)
            break
    if not domain:
        raise KnowledgeViewError("promotion target must be inside a declared profile domain folder")
    frontmatter = {
        "title": str(record["lens_id"]).replace("-", " ").title(),
        "type": "authoritative-record","status":"draft","markdown_category":"authoritative_markdown_source",
        "authority":"authoritative","domain":domain,"created":utc_now()[:10],"updated":utc_now()[:10],
        "promotion_provenance":{
            "source_view_id":view_id,"source_output_hash":record["output_hash"],
            "reviewer":reviewer_value,"reason":reason_value,"promoted_at":utc_now(),
        },
    }
    _write_atomic(target_path, "---\n" + yaml.safe_dump(frontmatter,sort_keys=False,allow_unicode=True) + "---\n\n" + body.lstrip())
    artifact_id = f"promoted_{hashlib.sha256(target_path.relative_to(root).as_posix().encode()).hexdigest()[:20]}"
    relationship_store = RelationshipStore(root)
    relationship_store.upsert_artifact({
        "artifact_id":artifact_id,"artifact_kind":"native-source","layer":"L0",
        "path":target_path.relative_to(root).as_posix(),"title":frontmatter["title"],
        "content_hash":hashlib.sha256(target_path.read_bytes()).hexdigest(),"lifecycle_state":"draft",
        "authority":"authoritative","metadata":{"promotion_provenance":frontmatter["promotion_provenance"]},
    })
    relationship_store.put_relationship(
        source_artifact_id=artifact_id,target_artifact_id=view_id,relationship_type="DERIVED_FROM",
        method="deterministic",method_version="explicit-promotion:v1",state="accepted",
        source_hash=hashlib.sha256(target_path.read_bytes()).hexdigest(),target_hash=record["output_hash"],
        evidence=[EvidenceAnchor(artifact_id,"frontmatter","promotion_provenance",hashlib.sha256(target_path.read_bytes()).hexdigest())],
    )
    return {"view_id":view_id,"artifact_id":artifact_id,"target":target_path.relative_to(root).as_posix(),"state":"authoritative-draft"}
