# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from mirrorarc.changes import journal
from mirrorarc.relationships.deterministic import refresh
from mirrorarc.relationships.model import EvidenceAnchor, RelationshipValidationError
from mirrorarc.relationships.proposals import propose
from mirrorarc.relationships.store import RelationshipStore


REPO_ROOT = Path(__file__).resolve().parents[1]


def copy_template(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    shutil.copytree(REPO_ROOT / "template", vault)
    source = vault / "20_sources" / "alpha.md"
    source.write_text(
        "---\ntitle: Alpha\ntype: authoritative-record\nstatus: active\ndomain: sources\n"
        "created: '2026-07-21'\nupdated: '2026-07-21'\n"
        "markdown_category: authoritative_markdown_source\nauthority: authoritative\n---\n\n"
        "Synthetic Alpha evidence.\n",
        encoding="utf-8",
    )
    second = vault / "20_sources" / "beta.md"
    second.write_text(source.read_text(encoding="utf-8").replace("Alpha", "Beta"), encoding="utf-8")
    return vault


def native_ids(store: RelationshipStore) -> list[str]:
    return [
        item["artifact_id"] for item in store.export()["artifacts"]
        if item["artifact_kind"] == "native-source"
    ]


def test_schema_migrates_existing_journal_database_without_losing_events(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)
    sequence = journal.record_event(vault, "modified", current_path="20_sources/alpha.md")

    store = RelationshipStore(vault)
    with store.connect() as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        component = conn.execute(
            "SELECT schema_version FROM derived_schema_meta WHERE component='relationships'"
        ).fetchone()[0]

    assert sequence == 1
    assert journal.get_event(vault, sequence)["current_path"] == "20_sources/alpha.md"  # type: ignore[index]
    assert {
        "journal_events", "artifacts", "relationships", "evidence_anchors",
        "relationship_reviews", "dependency_edges", "invalidation_records",
    } <= tables
    assert component == 1


def test_deterministic_refresh_and_rebuild_have_identical_fingerprint(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)
    first = refresh(vault)
    second = refresh(vault)
    store = RelationshipStore(vault)

    with store.connect() as conn:
        conn.execute("DELETE FROM relationships")
        conn.execute("DELETE FROM dependency_edges")
        conn.execute("DELETE FROM artifacts")
    rebuilt = refresh(vault)

    assert first["fingerprint"] == second["fingerprint"] == rebuilt["fingerprint"]
    status = store.status()
    assert status["relationships"]["by_state"] == {"accepted": status["relationships"]["total"]}
    assert status["evidence_anchors"] == status["relationships"]["total"]


def test_append_only_run_log_does_not_change_deterministic_graph(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)
    log = vault / "log.md"
    log.write_text(
        "---\ntitle: Run log\ntype: record\nstatus: active\nmarkdown_category: operational_control\n"
        "authority: operational\n---\n\n## First run\n",
        encoding="utf-8",
    )
    first = refresh(vault)

    log.write_text(log.read_text(encoding="utf-8") + "\n## Second run\n", encoding="utf-8")
    second = refresh(vault)

    assert first["fingerprint"] == second["fingerprint"]
    refreshed_paths = {
        item["path"]
        for item in RelationshipStore(vault).export()["artifacts"]
        if item["metadata"].get("deterministic_refresh")
    }
    assert "log.md" not in refreshed_paths


def test_semantic_relationship_requires_evidence_and_named_review_for_acceptance(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)
    refresh(vault)
    store = RelationshipStore(vault)
    source, target = native_ids(store)

    with pytest.raises(RelationshipValidationError, match="evidence"):
        store.put_relationship(
            source_artifact_id=source,
            target_artifact_id=target,
            relationship_type="SUPPORTS",
            method="model",
            method_version="1",
            state="proposed",
        )
    with pytest.raises(RelationshipValidationError, match="proposed"):
        store.put_relationship(
            source_artifact_id=source,
            target_artifact_id=target,
            relationship_type="SUPPORTS",
            method="model",
            method_version="1",
            state="accepted",
            evidence=[EvidenceAnchor(source, "line", "1", "hash", "Synthetic evidence")],
        )

    result = propose(
        vault,
        source_artifact_id=source,
        target_artifact_id=target,
        relationship_type="SUPPORTS",
        evidence_artifact_id=source,
        selector_type="line",
        selector_value="10-10",
        excerpt="Synthetic Alpha evidence.",
        confidence=0.8,
        method="model-proposal",
        method_version="fixture-v1",
        model_version="fixture-model",
        prompt_version="fixture-prompt",
    )
    proposed = next(
        item for item in store.export()["relationships"]
        if item["relationship_id"] == result["relationship_id"]
    )
    reviewed = store.review_relationship(
        result["relationship_id"], reviewer="fixture-reviewer", verdict="accepted", note="Evidence checked."
    )

    assert proposed["state"] == "proposed"
    assert proposed["model_version"] == "fixture-model"
    assert len(proposed["evidence"]) == 1
    assert reviewed["state"] == "accepted"
    accepted = next(
        item for item in store.export()["relationships"]
        if item["relationship_id"] == result["relationship_id"]
    )
    assert accepted["state"] == "accepted"
    assert accepted["reviews"][0]["reviewer"] == "fixture-reviewer"


def test_rejected_and_invalidated_relations_remain_auditable_but_not_current(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)
    refresh(vault)
    store = RelationshipStore(vault)
    source, target = native_ids(store)

    rejected = propose(
        vault, source_artifact_id=source, target_artifact_id=target,
        relationship_type="CONTRADICTS", evidence_artifact_id=source,
        selector_type="line", selector_value="1", excerpt="Synthetic conflict.",
    )
    store.review_relationship(rejected["relationship_id"], reviewer="reviewer", verdict="rejected")
    invalidated = propose(
        vault, source_artifact_id=target, target_artifact_id=source,
        relationship_type="MENTIONS", evidence_artifact_id=target,
        selector_type="line", selector_value="1", excerpt="Synthetic mention.",
    )
    store.invalidate_relationship(
        invalidated["relationship_id"], dependency_artifact_id=target,
        previous_hash="old", current_hash="new", reason="source hash changed", journal_sequence=7,
    )

    all_states = {
        item["relationship_id"]: item["state"] for item in store.export()["relationships"]
    }
    current_ids = {item["relationship_id"] for item in store.export(current_only=True)["relationships"]}

    assert all_states[rejected["relationship_id"]] == "rejected"
    assert all_states[invalidated["relationship_id"]] == "invalidated"
    assert rejected["relationship_id"] not in current_ids
    assert invalidated["relationship_id"] not in current_ids
    assert store.status()["invalidations"] == 1


def test_export_contains_metadata_and_bounded_anchors_not_source_bodies(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)
    refresh(vault)
    store = RelationshipStore(vault)
    source, target = native_ids(store)

    with pytest.raises(RelationshipValidationError, match="exceeds"):
        propose(
            vault, source_artifact_id=source, target_artifact_id=target,
            relationship_type="SAME_ENTITY", evidence_artifact_id=source,
            selector_type="line", selector_value="1", excerpt="x" * 1201,
        )

    payload = store.export()
    serialized = json.dumps(payload)
    assert "Synthetic Alpha evidence." not in serialized
    assert all("body" not in artifact for artifact in payload["artifacts"])


def test_relationship_cli_exposes_structured_refresh_status_and_export(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)

    refresh_result = subprocess.run(
        [sys.executable, "-m", "mirrorarc.cli", "--root", str(vault), "relationships", "refresh", "--json"],
        text=True, capture_output=True,
    )
    status_result = subprocess.run(
        [sys.executable, "-m", "mirrorarc.cli", "--root", str(vault), "relationships", "status", "--json"],
        text=True, capture_output=True,
    )
    export_result = subprocess.run(
        [sys.executable, "-m", "mirrorarc.cli", "--root", str(vault), "relationships", "export", "--current"],
        text=True, capture_output=True,
    )

    assert refresh_result.returncode == status_result.returncode == export_result.returncode == 0
    assert json.loads(refresh_result.stdout)["fingerprint"]
    assert json.loads(status_result.stdout)["relationships"]["total"] > 0
    assert json.loads(export_result.stdout)["relationships"]
