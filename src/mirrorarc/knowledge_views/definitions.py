# SPDX-License-Identifier: AGPL-3.0-or-later
"""Load and validate profile-owned knowledge-lens definitions."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from mirrorarc.runtime_profile import load_profile_mapping

REQUIRED_FIELDS = {
    "purpose", "audience", "source_query", "relationship_types", "output_sections",
    "max_tokens", "persistence", "citation_required",
}
PERSISTENCE_VALUES = {"ephemeral", "cache", "pinned", "reviewed"}


class LensDefinitionError(ValueError):
    """Raised when a lens contract is incomplete or unsafe."""


def canonical_definition(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def validate_lens(lens_id: str, value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise LensDefinitionError(f"knowledge_lenses.{lens_id} must be a mapping")
    missing = sorted(REQUIRED_FIELDS - set(value))
    if missing:
        raise LensDefinitionError(f"knowledge_lenses.{lens_id} missing: {', '.join(missing)}")
    if not isinstance(value["source_query"], dict):
        raise LensDefinitionError(f"knowledge_lenses.{lens_id}.source_query must be a mapping")
    for field in ("relationship_types", "output_sections"):
        if not isinstance(value[field], list) or any(not isinstance(item, str) for item in value[field]):
            raise LensDefinitionError(f"knowledge_lenses.{lens_id}.{field} must be a list of strings")
    if not isinstance(value["max_tokens"], int) or value["max_tokens"] < 100:
        raise LensDefinitionError(f"knowledge_lenses.{lens_id}.max_tokens must be an integer >= 100")
    if value["persistence"] not in PERSISTENCE_VALUES:
        raise LensDefinitionError(
            f"knowledge_lenses.{lens_id}.persistence must be one of: {', '.join(sorted(PERSISTENCE_VALUES))}"
        )
    if not isinstance(value["citation_required"], bool):
        raise LensDefinitionError(f"knowledge_lenses.{lens_id}.citation_required must be true or false")
    if value["persistence"] == "reviewed":
        raise LensDefinitionError(f"knowledge_lenses.{lens_id} cannot auto-persist as reviewed")
    result = dict(value)
    result["lens_id"] = lens_id
    result["definition_hash"] = hashlib.sha256(canonical_definition(value).encode("utf-8")).hexdigest()
    return result


def load_lenses(root: Path) -> dict[str, dict[str, Any]]:
    profile = load_profile_mapping(root.expanduser().resolve())
    raw = profile.get("knowledge_lenses", {}) if isinstance(profile, dict) else {}
    if not isinstance(raw, dict):
        raise LensDefinitionError("knowledge_lenses must be a mapping")
    return {str(lens_id): validate_lens(str(lens_id), value) for lens_id, value in sorted(raw.items())}


def get_lens(root: Path, lens_id: str) -> dict[str, Any]:
    lenses = load_lenses(root)
    if lens_id not in lenses:
        raise LensDefinitionError(f"unknown knowledge lens: {lens_id}")
    return lenses[lens_id]
