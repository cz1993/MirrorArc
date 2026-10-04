# SPDX-License-Identifier: AGPL-3.0-or-later
"""Relationship-ledger value validation and deterministic identities."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

DETERMINISTIC_TYPES = {
    "MIRRORS", "DERIVED_FROM", "IN_DOMAIN", "HAS_LIFECYCLE", "IN_PROFILE",
    "REVIEW_DEPENDS_ON", "IN_CONTEXT", "DEPENDS_ON", "INVALIDATES",
}
SEMANTIC_TYPES = {"MENTIONS", "SAME_ENTITY", "SUPPORTS", "CONTRADICTS", "SUPERSEDES", "GOVERNS"}
RELATIONSHIP_TYPES = DETERMINISTIC_TYPES | SEMANTIC_TYPES
RELATIONSHIP_STATES = {"proposed", "accepted", "rejected", "invalidated"}
REVIEW_VERDICTS = {"accepted", "rejected"}
MAX_EVIDENCE_CHARS = 1200


class RelationshipValidationError(ValueError):
    """Raised when a relationship would violate evidence or state contracts."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()[:28]
    return f"{prefix}_{digest}"


def relationship_id(
    source_artifact_id: str,
    relationship_type: str,
    target_artifact_id: str,
    method: str,
    method_version: str,
) -> str:
    return stable_id(
        "rel", source_artifact_id, relationship_type, target_artifact_id, method, method_version
    )


def evidence_id(relationship: str, artifact_id: str, selector_type: str, selector_value: str) -> str:
    return stable_id("ev", relationship, artifact_id, selector_type, selector_value)


def validate_relationship_type(value: str) -> str:
    normalized = value.strip().upper()
    if normalized not in RELATIONSHIP_TYPES:
        raise RelationshipValidationError(f"unsupported relationship type: {value}")
    return normalized


def validate_state(value: str) -> str:
    normalized = value.strip().lower()
    if normalized not in RELATIONSHIP_STATES:
        raise RelationshipValidationError(f"unsupported relationship state: {value}")
    return normalized


def bounded_evidence(value: str) -> str:
    text = value.strip()
    if len(text) > MAX_EVIDENCE_CHARS:
        raise RelationshipValidationError(
            f"evidence anchor exceeds {MAX_EVIDENCE_CHARS} characters"
        )
    return text


@dataclass(frozen=True)
class EvidenceAnchor:
    artifact_id: str
    selector_type: str
    selector_value: str
    source_hash: str
    excerpt: str = ""

    def validate(self) -> "EvidenceAnchor":
        if not self.artifact_id.strip():
            raise RelationshipValidationError("evidence artifact_id is required")
        if not self.selector_type.strip() or not self.selector_value.strip():
            raise RelationshipValidationError("evidence selector type and value are required")
        bounded_evidence(self.excerpt)
        return self
