# SPDX-License-Identifier: AGPL-3.0-or-later
"""Admission boundary for optional semantic relationship proposals."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from mirrorarc.relationships.model import EvidenceAnchor, RelationshipValidationError
from mirrorarc.relationships.store import RelationshipStore


def propose(
    root: Path,
    *,
    source_artifact_id: str,
    target_artifact_id: str,
    relationship_type: str,
    evidence_artifact_id: str,
    selector_type: str,
    selector_value: str,
    excerpt: str = "",
    confidence: float | None = None,
    method: str = "rule-proposal",
    method_version: str = "1",
    model_version: str = "",
    prompt_version: str = "",
) -> dict[str, Any]:
    store = RelationshipStore(root)
    artifacts = {item["artifact_id"]: item for item in store.export()["artifacts"]}
    for artifact_id in (source_artifact_id, target_artifact_id, evidence_artifact_id):
        if artifact_id not in artifacts:
            raise RelationshipValidationError(f"unknown artifact_id: {artifact_id}")
    source = artifacts[source_artifact_id]
    target = artifacts[target_artifact_id]
    evidence_artifact = artifacts[evidence_artifact_id]
    relationship = store.put_relationship(
        source_artifact_id=source_artifact_id,
        target_artifact_id=target_artifact_id,
        relationship_type=relationship_type,
        method=method,
        method_version=method_version,
        state="proposed",
        source_hash=str(source.get("content_hash", "") or ""),
        target_hash=str(target.get("content_hash", "") or ""),
        confidence=confidence,
        model_version=model_version,
        prompt_version=prompt_version,
        evidence=[EvidenceAnchor(
            artifact_id=evidence_artifact_id,
            selector_type=selector_type,
            selector_value=selector_value,
            source_hash=str(evidence_artifact.get("content_hash", "") or ""),
            excerpt=excerpt,
        )],
    )
    return {"relationship_id": relationship, "state": "proposed"}
