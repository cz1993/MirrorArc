# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded dependency invalidation driven by applied journal events and reconciliation."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from mirrorarc.changes import journal
from mirrorarc.relationships.deterministic import refresh_source_record
from mirrorarc.relationships.model import stable_id
from mirrorarc.relationships.store import RelationshipStore, utc_now


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def apply_source_event(
    root: Path,
    event: dict[str, Any],
    materialization: dict[str, Any],
    *,
    previous_hash: str = "",
    max_depth: int = 16,
    max_nodes: int = 1000,
) -> dict[str, Any]:
    """Update the affected L0/L1 subgraph and invalidate hash-bound dependents."""
    record = materialization.get("record")
    if not isinstance(record, dict) or not record.get("source_id"):
        return {"applied": False, "reason": "no-source-identity", "invalidated": 0, "affected": []}
    root = root.expanduser().resolve()
    source_id = str(record["source_id"])
    current_hash = str(record.get("source_sha256", "") or "")
    projection_id = str(record.get("projection_id", "") or "")
    if not projection_id:
        from mirrorarc.knowledge_inventory import stable_projection_id
        projection_id = stable_projection_id(source_id)
    graph_update = refresh_source_record(root, record)
    store = RelationshipStore(root)
    move_only = str(event.get("event_kind", "")) == "moved" and previous_hash and previous_hash == current_hash
    hash_changed = bool(previous_hash and previous_hash != current_hash)
    deleted = str(event.get("event_kind", "")) == "deleted"
    if not hash_changed and not deleted:
        return {
            "applied": True, "reason": "move-only" if move_only else "hash-unchanged",
            "invalidated": 0, "affected": [], "graph_update": graph_update,
        }

    roots = {source_id, projection_id}
    traversal = store.affected_dependents(roots, max_depth=max_depth, max_nodes=max_nodes)
    invalidated_relationships: list[str] = []
    sequence = int(event.get("sequence", 0) or 0) or None
    reason = "source deleted" if deleted else "source hash changed"
    with store.connect() as conn:
        candidates = conn.execute(
            """
            SELECT DISTINCT r.relationship_id
              FROM relationships r
              LEFT JOIN evidence_anchors e ON e.relationship_id = r.relationship_id
             WHERE r.method <> 'deterministic'
               AND r.state NOT IN ('rejected','invalidated')
               AND (r.source_artifact_id IN (?, ?) OR r.target_artifact_id IN (?, ?) OR e.artifact_id IN (?, ?))
               AND (? = '' OR r.source_hash = ? OR r.target_hash = ? OR e.source_hash = ?)
            """,
            (
                source_id, projection_id, source_id, projection_id, source_id, projection_id,
                previous_hash, previous_hash, previous_hash, previous_hash,
            ),
        ).fetchall()
    for row in candidates:
        relationship_id = str(row[0])
        store.invalidate_relationship(
            relationship_id,
            dependency_artifact_id=source_id,
            previous_hash=previous_hash,
            current_hash=current_hash,
            reason=reason,
            journal_sequence=sequence,
        )
        invalidated_relationships.append(relationship_id)

    affected = traversal["affected"]
    with store.connect() as conn:
        dependency_relationships = conn.execute(
            "SELECT relationship_id FROM relationships WHERE state NOT IN ('rejected','invalidated') "
            "AND relationship_type IN ('DEPENDS_ON','REVIEW_DEPENDS_ON','IN_CONTEXT') "
            f"AND source_artifact_id IN ({','.join('?' for _ in affected)})" if affected else
            "SELECT relationship_id FROM relationships WHERE 0",
            tuple(affected),
        ).fetchall()
    for row in dependency_relationships:
        relationship_id = str(row[0])
        store.invalidate_relationship(
            relationship_id, dependency_artifact_id=source_id,
            previous_hash=previous_hash, current_hash=current_hash,
            reason=reason, journal_sequence=sequence,
        )
        invalidated_relationships.append(relationship_id)
    now = utc_now()
    with store.connect() as conn:
        for artifact_id in affected:
            invalidation_id = stable_id(
                "inv", artifact_id, source_id, previous_hash, current_hash, str(sequence or 0), reason
            )
            conn.execute(
                "INSERT OR IGNORE INTO invalidation_records(invalidation_id, artifact_id, dependency_artifact_id, previous_hash, current_hash, reason, journal_sequence, invalidated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (invalidation_id, artifact_id, source_id, previous_hash, current_hash, reason, sequence, now),
            )
            if _table_exists(conn, "knowledge_views"):
                conn.execute(
                    """
                    UPDATE knowledge_views
                       SET state=CASE WHEN state='reviewed' THEN 'stale' ELSE state END,
                           refresh_queued=CASE WHEN state='generated' THEN 1 ELSE refresh_queued END,
                           stale_reason=?, updated_at=?
                     WHERE view_id=?
                    """,
                    (reason, now, artifact_id),
                )
            if _table_exists(conn, "context_packs"):
                conn.execute(
                    "UPDATE context_packs SET freshness_state='stale', stale_reason=?, updated_at=? WHERE context_id=? AND mode='frozen'",
                    (reason, now, artifact_id),
                )
    return {
        "applied": True,
        "reason": reason,
        "source_id": source_id,
        "projection_id": projection_id,
        "previous_hash": previous_hash,
        "current_hash": current_hash,
        "journal_sequence": sequence,
        "invalidated": len(invalidated_relationships) + len(affected),
        "invalidated_relationships": invalidated_relationships,
        "affected": affected,
        "traversal": traversal,
        "graph_update": graph_update,
    }


def reconcile_derived_state(root: Path, *, max_depth: int = 16, max_nodes: int = 1000) -> dict[str, Any]:
    """Repair missed invalidations when manifest hashes differ from ledger artifact hashes."""
    root = root.expanduser().resolve()
    path = journal.state_db_path(root)
    if not path.exists():
        return {"checked": 0, "repaired": 0, "items": []}
    conn = sqlite3.connect(path)
    try:
        if not _table_exists(conn, "artifacts"):
            return {"checked": 0, "repaired": 0, "items": []}
        artifact_hashes = {str(row[0]): str(row[1] or "") for row in conn.execute(
            "SELECT artifact_id, content_hash FROM artifacts WHERE artifact_kind='source'"
        )}
    finally:
        conn.close()
    manifest_path = root / "_meta" / "source-manifest.json"
    if not manifest_path.exists():
        return {"checked": 0, "repaired": 0, "items": []}
    try:
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"checked": 0, "repaired": 0, "items": []}
    records = value.get("records", []) if isinstance(value, dict) else []
    items: list[dict[str, Any]] = []
    checked = 0
    for record in records if isinstance(records, list) else []:
        if not isinstance(record, dict):
            continue
        source_id = str(record.get("source_id", "") or "")
        if source_id not in artifact_hashes:
            continue
        checked += 1
        previous_hash = artifact_hashes[source_id]
        current_hash = str(record.get("source_sha256", "") or "")
        current_state = str(record.get("lifecycle_state", "") or "")
        if previous_hash == current_hash and current_state != "source_missing":
            continue
        event = {
            "sequence": 0,
            "event_kind": "deleted" if current_state == "source_missing" else "reconciled",
        }
        items.append(apply_source_event(
            root, event, {"record": record}, previous_hash=previous_hash,
            max_depth=max_depth, max_nodes=max_nodes,
        ))
    return {"checked": checked, "repaired": len(items), "items": items}
