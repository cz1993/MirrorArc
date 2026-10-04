# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from mirrorarc.migration import apply_markdown_review, markdown_inventory, markdown_summary


REPO_ROOT = Path(__file__).resolve().parents[1]


def copy_template(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    shutil.copytree(REPO_ROOT / "template", vault)
    return vault


def markdown(title: str, note_type: str, *, category: str = "") -> str:
    category_line = f"markdown_category: {category}\n" if category else ""
    return (
        "---\n"
        f"title: {title}\n"
        f"type: {note_type}\n"
        "status: active\n"
        "domain: sources\n"
        "created: '2026-07-21'\n"
        "updated: '2026-07-21'\n"
        f"{category_line}"
        "---\n\n"
        f"# {title}\n"
    )


def test_markdown_inventory_classifies_every_file_deterministically(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)
    source = vault / "20_sources" / "native.md"
    source.write_text(markdown("Native", "authoritative-record"), encoding="utf-8")
    legacy = vault / "20_sources" / "legacy.md"
    legacy.write_text(markdown("Legacy", "note"), encoding="utf-8")
    unknown = vault / "20_sources" / "unknown.md"
    unknown.write_text(markdown("Unknown", "mystery"), encoding="utf-8")
    mirror = vault / "_mirrors" / "source.docx.md"
    mirror.parent.mkdir(exist_ok=True)
    mirror.write_text(markdown("Mirror", "source-mirror") + "\n%% AUTO-GENERATED BELOW — DO NOT EDIT %%\n", encoding="utf-8")

    first = markdown_inventory(vault)
    second = markdown_inventory(vault)

    assert first == second
    by_path = {item["path"]: item for item in first}
    assert by_path["INDEX.md"]["category"] == "index"
    assert by_path["20_sources/native.md"]["category"] == "authoritative_markdown_source"
    assert by_path["20_sources/legacy.md"]["category"] == "legacy_curated_derivative"
    assert by_path["20_sources/unknown.md"]["category"] == "unknown"
    assert by_path["_mirrors/source.docx.md"]["category"] == "l1_projection"
    assert by_path["_meta/agent-rules.md"]["category"] == "operational_control"
    summary = markdown_summary(first)
    assert summary["total"] == len(first)
    assert summary["unexplained"] == 1


def test_template_markdown_inventory_has_no_unexplained_files(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)

    summary = markdown_summary(markdown_inventory(vault))

    assert summary["unexplained"] == 0


def test_reviewed_write_requires_hash_and_external_backup_and_is_idempotent(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)
    target = vault / "20_sources" / "legacy.md"
    original = markdown("Legacy", "note")
    target.write_text(original, encoding="utf-8")
    unrelated = vault / "20_sources" / "unrelated.md"
    unrelated_text = markdown("Unrelated", "authoritative-record")
    unrelated.write_text(unrelated_text, encoding="utf-8")
    expected = hashlib.sha256(original.encode("utf-8")).hexdigest()
    review_path = tmp_path / "review.json"
    review_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "reviewed": True,
                "reviewer": "operator",
                "items": [
                    {
                        "path": "20_sources/legacy.md",
                        "expected_sha256": expected,
                        "action": "set_category",
                        "category": "authoritative_markdown_source",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    backup = tmp_path / "backup"

    planned = apply_markdown_review(vault, review_path, backup, write=False)
    applied = apply_markdown_review(vault, review_path, backup, write=True)
    repeated = apply_markdown_review(vault, review_path, backup, write=True)

    assert planned["summary"]["planned"] == 1
    assert applied["summary"]["updated"] == 1
    assert repeated["summary"]["unchanged"] == 1
    assert "markdown_category: authoritative_markdown_source" in target.read_text(encoding="utf-8")
    assert (backup / "20_sources" / "legacy.md").read_text(encoding="utf-8") == original
    assert unrelated.read_text(encoding="utf-8") == unrelated_text

    with pytest.raises(ValueError, match="outside the vault"):
        apply_markdown_review(vault, review_path, vault / "_backup", write=True)


def test_reviewed_write_fails_closed_on_changed_hash(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)
    target = vault / "20_sources" / "legacy.md"
    target.write_text(markdown("Legacy", "note"), encoding="utf-8")
    review_path = tmp_path / "review.json"
    review_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "reviewed": True,
                "reviewer": "operator",
                "items": [
                    {
                        "path": "20_sources/legacy.md",
                        "expected_sha256": "0" * 64,
                        "action": "set_category",
                        "category": "authoritative_markdown_source",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = apply_markdown_review(vault, review_path, tmp_path / "backup", write=True)

    assert result["summary"]["errors"] == 1
    assert "markdown_category" not in target.read_text(encoding="utf-8")
