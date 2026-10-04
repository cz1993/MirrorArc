# SPDX-License-Identifier: AGPL-3.0-or-later
"""Deterministic, cited, budgeted rendering for profile-owned L2 lenses."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Protocol

from mirrorarc.knowledge_views.definitions import get_lens
from mirrorarc.knowledge_views.store import KnowledgeViewStore
from mirrorarc.relationships.model import EvidenceAnchor, canonical_json, stable_id
from mirrorarc.relationships.store import RelationshipStore

CACHE_ROOT = Path(".mirrorarc/cache/views")
MAX_ITEM_EXCERPT = 1200
DETERMINISTIC_RENDERER_VERSION = "deterministic-view:v3"


class ViewSynthesizer(Protocol):
    model_version: str
    prompt_version: str

    def render(self, *, lens: dict[str, Any], evidence: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> str: ...


def _safe_path(root: Path, rel: str) -> Path | None:
    candidate = Path(rel)
    if not rel or candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (root / candidate).resolve()
    if not resolved.is_relative_to(root) or resolved.is_symlink() or not resolved.is_file():
        return None
    return resolved


def _excerpt(root: Path, rel: str, limit: int = MAX_ITEM_EXCERPT) -> str:
    path = _safe_path(root, rel)
    if path is None or path.suffix.lower() not in {".md", ".txt", ".csv", ".tsv", ".json", ".yaml", ".yml"}:
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4:]
    marker = "%% AUTO-GENERATED BELOW — DO NOT EDIT %%"
    if marker in text:
        text = text.split(marker, 1)[1]
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    return " ".join(lines)[:limit]


def _select_evidence(root: Path, lens: dict[str, Any], graph: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    artifacts = {item["artifact_id"]: item for item in graph["artifacts"]}
    current_relationships = graph["relationships"]
    projections = {
        item["target_artifact_id"]: artifacts.get(item["source_artifact_id"])
        for item in current_relationships
        if item["relationship_type"] == "MIRRORS" and item["state"] == "accepted"
    }
    query = lens["source_query"]
    domains = {str(value) for value in query.get("domains", [])} if isinstance(query.get("domains", []), list) else set()
    freshness = str(query.get("freshness", "") or "")
    candidates: list[dict[str, Any]] = []
    for artifact in artifacts.values():
        if artifact["artifact_kind"] not in {"source", "native-source", "repository"}:
            continue
        if artifact["lifecycle_state"] in {"source_missing", "archived", "superseded"}:
            continue
        if domains and artifact["domain"] not in domains:
            continue
        if freshness == "changed" and artifact["lifecycle_state"] in {"clean", "current", "active"}:
            continue
        projection = projections.get(artifact["artifact_id"])
        readable_path = str((projection or artifact).get("path", "") or "")
        candidates.append({
            "artifact_id": artifact["artifact_id"],
            "title": artifact["title"],
            "source_path": artifact["path"],
            "readable_path": readable_path,
            "content_hash": artifact["content_hash"],
            "projection_id": str((projection or {}).get("artifact_id", "") or ""),
            "projection_hash": str((projection or {}).get("content_hash", "") or ""),
            "domain": artifact["domain"],
            "excerpt": _excerpt(root, readable_path),
        })
    priority_paths = [str(value) for value in query.get("priority_paths", []) if isinstance(value, str)]
    priority = {path: index for index, path in enumerate(priority_paths)}
    candidates.sort(key=lambda item: (
        item["domain"], priority.get(item["source_path"], len(priority)),
        item["source_path"], item["artifact_id"],
    ))
    # A broad lens must not exhaust its budget in the alphabetically first domain. Interleave
    # profile domains deterministically so orientation/change views retain cross-domain evidence.
    by_domain: dict[str, list[dict[str, Any]]] = {}
    for item in candidates:
        by_domain.setdefault(item["domain"] or "unclassified", []).append(item)
    candidates = []
    for index in range(max((len(items) for items in by_domain.values()), default=0)):
        for domain in sorted(by_domain):
            if index < len(by_domain[domain]):
                candidates.append(by_domain[domain][index])
    allowed_types = {str(value).upper() for value in lens["relationship_types"]}
    selected_ids = {item["artifact_id"] for item in candidates}
    related = [
        item for item in current_relationships
        if item["relationship_type"] in allowed_types
        and (item["source_artifact_id"] in selected_ids or item["target_artifact_id"] in selected_ids)
    ]
    return candidates, related


def _deterministic_markdown(
    lens: dict[str, Any], evidence: list[dict[str, Any]], relationships: list[dict[str, Any]]
) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    char_budget = int(lens["max_tokens"]) * 4
    lines = [
        f"# {lens['lens_id'].replace('-', ' ').title()}", "",
        f"> Purpose: {lens['purpose']}",
        f"> Audience: {lens['audience']}",
        "> Generated from governed current evidence; cited records remain authoritative.", "",
    ]
    citations: list[dict[str, Any]] = []
    omitted: list[dict[str, Any]] = []
    sections = [str(value) for value in lens["output_sections"]]
    for section in sections:
        lines.extend([f"## {section.replace('-', ' ').title()}", ""])
        if section in {"scope", "next-actions", "review-work"}:
            lines.append(f"This view selected {len(evidence)} governed source record(s) for `{lens['lens_id']}`.")
            lines.append("")
            continue
        if section in {"relationships", "impact", "stale-views"}:
            if relationships:
                relation_priority = {
                    "GOVERNS": 0, "CONTRADICTS": 1, "SUPPORTS": 2, "SUPERSEDES": 3,
                    "MIRRORS": 4, "DERIVED_FROM": 5, "DEPENDS_ON": 6, "IN_DOMAIN": 20,
                }
                ordered = sorted(relationships, key=lambda item: (
                    relation_priority.get(item["relationship_type"], 10),
                    item["source_artifact_id"], item["target_artifact_id"],
                ))
                in_domain = 0
                rendered = 0
                for relation in ordered:
                    if relation["relationship_type"] == "IN_DOMAIN":
                        if in_domain >= 8:
                            continue
                        in_domain += 1
                    lines.append(
                        f"- `{relation['relationship_type']}`: `{relation['source_artifact_id']}` → "
                        f"`{relation['target_artifact_id']}` ({relation['state']}, {relation['method']})"
                    )
                    rendered += 1
                    if rendered >= 40:
                        break
            else:
                lines.append("- No eligible current relationships matched this lens.")
            lines.append("")
            continue
        included = 0
        for item in evidence:
            excerpt = item["excerpt"] or "No readable excerpt is stored; inspect the cited source/projection."
            block = [
                f"### {item['title'] or Path(item['source_path']).stem}", "",
                f"- Source: `{item['source_path']}`",
                f"- Readable evidence: `{item['readable_path']}`",
                f"- SHA-256/state hash: `{item['content_hash']}`", "",
                excerpt, "",
            ]
            candidate = "\n".join([*lines, *block])
            if len(candidate) > char_budget:
                omitted.append({"artifact_id": item["artifact_id"], "reason": "token_budget"})
                continue
            lines.extend(block)
            citations.append({
                "artifact_id": item["artifact_id"], "source_path": item["source_path"],
                "readable_path": item["readable_path"], "source_hash": item["content_hash"],
                "projection_id": item["projection_id"], "projection_hash": item["projection_hash"],
            })
            included += 1
        if included == 0:
            lines.extend(["No evidence item fit the declared budget.", ""])
    if omitted:
        lines.extend(["## Omissions", ""])
        lines.extend(f"- `{item['artifact_id']}` — {item['reason']}" for item in omitted)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n", citations, omitted


def _write_atomic(path: Path, text: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(text, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return True


def render_lens(
    root: Path,
    lens_id: str,
    *,
    synthesizer: ViewSynthesizer | None = None,
) -> dict[str, Any]:
    root = root.expanduser().resolve()
    lens = get_lens(root, lens_id)
    relationship_store = RelationshipStore(root)
    graph = relationship_store.export(current_only=True)
    evidence, relationships = _select_evidence(root, lens, graph)
    dependencies = [
        {
            "artifact_id": item["artifact_id"], "content_hash": item["content_hash"],
            "projection_id": item["projection_id"], "projection_hash": item["projection_hash"],
        }
        for item in evidence
    ]
    dependency_hash = hashlib.sha256(canonical_json({
        "renderer_version": DETERMINISTIC_RENDERER_VERSION,
        "dependencies": dependencies,
    }).encode("utf-8")).hexdigest()
    view_id = stable_id("view", lens_id, lens["definition_hash"], dependency_hash)
    store = KnowledgeViewStore(root)
    store.stale_reviewed_except(
        lens_id,
        lens["definition_hash"],
        dependency_hash,
        reason="lens definition or selected dependency snapshot changed",
    )
    existing = store.find_by_dependency(lens_id, lens["definition_hash"], dependency_hash)
    if existing and (root / existing["output_path"]).is_file():
        return {**existing, "unchanged": True, "omitted": []}
    if synthesizer is None:
        markdown, citations, omitted = _deterministic_markdown(lens, evidence, relationships)
        generation_method = "deterministic"
        model_version = ""
        prompt_version = ""
    else:
        markdown = synthesizer.render(lens=lens, evidence=evidence, relationships=relationships)
        citations = [
            {key: item[key] for key in ("artifact_id", "source_path", "readable_path", "content_hash")}
            for item in evidence
        ]
        omitted = []
        generation_method = "model-assisted"
        model_version = synthesizer.model_version
        prompt_version = synthesizer.prompt_version
    output_hash = hashlib.sha256(markdown.encode("utf-8")).hexdigest()
    output_rel = CACHE_ROOT / f"{view_id}.md"
    wrote = _write_atomic(root / output_rel, markdown)
    version = store.next_version(lens_id)
    result = store.register(
        view_id=view_id,lens_id=lens_id,definition_hash=lens["definition_hash"],
        dependency_hash=dependency_hash,state="generated",version=version,
        output_path=output_rel.as_posix(),output_hash=output_hash,citations=citations,
        generation_method=generation_method,model_version=model_version,prompt_version=prompt_version,
        persistence=str(lens["persistence"]),
    )
    store.supersede_generated(lens_id, view_id)
    view_artifact = {
        "artifact_id": view_id,"artifact_kind":"knowledge-view","layer":"L2",
        "path":output_rel.as_posix(),"title":lens_id,"content_hash":output_hash,
        "lifecycle_state":"generated","authority":"derived",
        "metadata":{"lens_id":lens_id,"definition_hash":lens["definition_hash"],"dependency_hash":dependency_hash,"version":version},
    }
    relation_specs: list[dict[str, Any]] = []
    for item in dependencies:
        relation_specs.append({
            "source_artifact_id":view_id,"target_artifact_id":item["artifact_id"],
            "relationship_type":"DEPENDS_ON","method":"deterministic","method_version":"knowledge-view:v1",
            "state":"accepted","source_hash":output_hash,"target_hash":item["content_hash"],
            "evidence":[EvidenceAnchor(view_id,"citation",item["artifact_id"],output_hash)],
        })
    relationship_store.replace_deterministic_for_artifacts({view_id}, [view_artifact], relation_specs)
    with relationship_store.connect() as conn:
        superseded_ids = [view["view_id"] for view in store.list(lens_id=lens_id) if view["state"] == "superseded"]
        if superseded_ids:
            conn.executemany(
                "UPDATE artifacts SET lifecycle_state='superseded',updated_at=datetime('now') WHERE artifact_id=?",
                [(item,) for item in superseded_ids],
            )
        for item in dependencies:
            conn.execute(
                "INSERT OR REPLACE INTO dependency_edges(dependent_artifact_id,dependency_artifact_id,dependency_kind,dependency_hash,created_at) VALUES (?,?,?,?,datetime('now'))",
                (view_id,item["artifact_id"],"view-input",item["content_hash"]),
            )
    return {**result,"unchanged":not wrote,"omitted":omitted}
