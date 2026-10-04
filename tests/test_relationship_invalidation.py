# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

import shutil
from pathlib import Path

from mirrorarc.changes import journal, materialize, worker
from mirrorarc.relationships.invalidation import apply_source_event, reconcile_derived_state
from mirrorarc.relationships.model import EvidenceAnchor
from mirrorarc.relationships.store import RelationshipStore


REPO_ROOT = Path(__file__).resolve().parents[1]


class FixtureConverter:
    def __init__(self) -> None:
        self.paths: list[str] = []

    class Result:
        text_content = "Synthetic extracted evidence."

    def convert(self, path: str) -> "FixtureConverter.Result":
        self.paths.append(path)
        return self.Result()


def copy_template(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    shutil.copytree(REPO_ROOT / "template", vault)
    return vault


def initial_source(vault: Path) -> tuple[Path, dict, FixtureConverter]:
    source = vault / "20_sources" / "evidence.docx"
    source.write_bytes(b"synthetic source version one")
    converter = FixtureConverter()
    sequence = journal.record_event(vault, "created", current_path="20_sources/evidence.docx")
    result = worker.process_next_event(
        vault, "fixture-worker", materialize_kwargs={
            "converter": converter, "converter_name": "fixture", "converter_version": "1",
            "append_audit": False,
        }
    )
    assert result["finish_status"] == "applied"
    assert result["event"]["sequence"] == sequence
    return source, result["materialization"]["record"], converter


def add_semantic_relation(store: RelationshipStore, record: dict) -> str:
    source_id = record["source_id"]
    projection_id = record["projection_id"]
    return store.put_relationship(
        source_artifact_id=source_id,
        target_artifact_id=projection_id,
        relationship_type="MENTIONS",
        method="fixture-semantic",
        method_version="1",
        state="proposed",
        source_hash=record["source_sha256"],
        target_hash=record["generated_region_sha256"],
        evidence=[EvidenceAnchor(
            artifact_id=source_id, selector_type="paragraph", selector_value="1",
            source_hash=record["source_sha256"], excerpt="Synthetic evidence anchor.",
        )],
    )


def add_dependency_fixture(store: RelationshipStore, source_id: str) -> None:
    for artifact_id, kind in (
        ("view_reviewed", "knowledge-view"),
        ("view_generated", "knowledge-view"),
        ("context_frozen", "context"),
        ("context_dynamic", "context"),
        ("view_unrelated", "knowledge-view"),
        ("source_unrelated", "source"),
    ):
        store.upsert_artifact({
            "artifact_id": artifact_id, "artifact_kind": kind,
            "layer": "L2" if kind == "knowledge-view" else "context",
            "content_hash": artifact_id, "authority": "derived",
        })
    with store.connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS knowledge_views (
              view_id TEXT PRIMARY KEY, state TEXT NOT NULL, refresh_queued INTEGER NOT NULL DEFAULT 0,
              stale_reason TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS context_packs (
              context_id TEXT PRIMARY KEY, mode TEXT NOT NULL, freshness_state TEXT NOT NULL,
              stale_reason TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL
            );
            """
        )
        conn.executemany(
            "INSERT INTO knowledge_views(view_id,state,refresh_queued,stale_reason,updated_at) VALUES (?,?,0,'','now')",
            [("view_reviewed", "reviewed"), ("view_generated", "generated"), ("view_unrelated", "reviewed")],
        )
        conn.executemany(
            "INSERT INTO context_packs(context_id,mode,freshness_state,stale_reason,updated_at) VALUES (?,?, 'current','','now')",
            [("context_frozen", "frozen"), ("context_dynamic", "dynamic")],
        )
        conn.executemany(
            "INSERT INTO dependency_edges(dependent_artifact_id,dependency_artifact_id,dependency_kind,dependency_hash,created_at) VALUES (?,?,?,?, 'now')",
            [
                ("view_reviewed", source_id, "view-input", "old"),
                ("view_generated", source_id, "view-input", "old"),
                ("context_frozen", "view_reviewed", "context-input", "old"),
                ("context_dynamic", "view_reviewed", "context-input", "old"),
                ("view_reviewed", "context_dynamic", "cycle-fixture", "old"),
                ("view_unrelated", "source_unrelated", "view-input", "other"),
            ],
        )


def test_applied_source_change_invalidates_only_bounded_dependents(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)
    source, record, _initial_converter = initial_source(vault)
    store = RelationshipStore(vault)
    relationship_id = add_semantic_relation(store, record)
    store.review_relationship(relationship_id, reviewer="fixture-reviewer", verdict="accepted")
    add_dependency_fixture(store, record["source_id"])
    source.write_bytes(b"synthetic source version two")
    converter = FixtureConverter()
    sequence = journal.record_event(
        vault, "modified", current_path="20_sources/evidence.docx", source_id=record["source_id"]
    )

    result = worker.process_next_event(
        vault, "fixture-worker", materialize_kwargs={
            "converter": converter, "converter_name": "fixture", "converter_version": "1",
            "append_audit": False,
        }
    )

    assert result["finish_status"] == "applied"
    assert converter.paths == [str(source)]
    invalidation = result["invalidation"]
    assert invalidation["journal_sequence"] == sequence
    assert invalidation["traversal"]["truncated"] is False
    assert set(invalidation["affected"]) == {
        "view_reviewed", "view_generated", "context_frozen", "context_dynamic",
    }
    relation = next(
        item for item in store.export()["relationships"] if item["relationship_id"] == relationship_id
    )
    assert relation["state"] == "invalidated"
    with store.connect() as conn:
        views = {row[0]: (row[1], row[2]) for row in conn.execute(
            "SELECT view_id,state,refresh_queued FROM knowledge_views"
        )}
        contexts = {row[0]: row[1] for row in conn.execute(
            "SELECT context_id,freshness_state FROM context_packs"
        )}
        sequences = {row[0] for row in conn.execute(
            "SELECT journal_sequence FROM invalidation_records WHERE journal_sequence IS NOT NULL"
        )}
    assert views["view_reviewed"] == ("stale", 0)
    assert views["view_generated"] == ("generated", 1)
    assert views["view_unrelated"] == ("reviewed", 0)
    assert contexts["context_frozen"] == "stale"
    assert contexts["context_dynamic"] == "current"
    assert sequence in sequences


def test_move_only_refresh_preserves_accepted_semantic_relation(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)
    _source, record, _converter = initial_source(vault)
    store = RelationshipStore(vault)
    relationship_id = add_semantic_relation(store, record)
    store.review_relationship(relationship_id, reviewer="fixture-reviewer", verdict="accepted")
    moved = dict(record)
    moved["current_source_path"] = "20_sources/moved-evidence.docx"

    report = apply_source_event(
        vault,
        {"sequence": 2, "event_kind": "moved"},
        {"record": moved},
        previous_hash=record["source_sha256"],
    )

    relation = next(
        item for item in store.export()["relationships"] if item["relationship_id"] == relationship_id
    )
    source_artifact = next(
        item for item in store.export()["artifacts"] if item["artifact_id"] == record["source_id"]
    )
    assert report["reason"] == "move-only"
    assert report["invalidated"] == 0
    assert relation["state"] == "accepted"
    assert source_artifact["path"] == "20_sources/moved-evidence.docx"


def test_reconciliation_repairs_missed_hash_invalidation(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)
    source, record, _converter = initial_source(vault)
    store = RelationshipStore(vault)
    relationship_id = add_semantic_relation(store, record)
    store.review_relationship(relationship_id, reviewer="fixture-reviewer", verdict="accepted")
    source.write_bytes(b"synthetic source changed outside journal")
    direct = materialize.materialize_office_source(
        vault, "20_sources/evidence.docx", converter=FixtureConverter(),
        converter_name="fixture", converter_version="1", append_audit=False,
    )
    assert direct["status"] == "updated"

    repair = reconcile_derived_state(vault)

    relation = next(
        item for item in store.export()["relationships"] if item["relationship_id"] == relationship_id
    )
    assert repair["checked"] == 1
    assert repair["repaired"] == 1
    assert relation["state"] == "invalidated"
