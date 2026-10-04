# SPDX-License-Identifier: AGPL-3.0-or-later
"""Versioned SQLite repository for relationships, evidence, dependencies, and invalidation."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from mirrorarc.changes import journal
from mirrorarc.relationships.model import (
    DETERMINISTIC_TYPES,
    EvidenceAnchor,
    RelationshipValidationError,
    REVIEW_VERDICTS,
    bounded_evidence,
    canonical_json,
    evidence_id,
    relationship_id,
    stable_id,
    validate_relationship_type,
    validate_state,
)

RELATIONSHIP_SCHEMA_VERSION = 1
SCHEMA_COMPONENT = "relationships"


def utc_now() -> str:
    return journal.utc_now()


class RelationshipStore:
    """Operate on relationship state inside the existing MirrorArc local database."""

    def __init__(self, root: Path):
        self.root = root.expanduser().resolve()

    @property
    def path(self) -> Path:
        return journal.state_db_path(self.root)

    def connect(self) -> sqlite3.Connection:
        journal.initialize(self.root)
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        self._migrate(conn)
        return conn

    def _migrate(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS derived_schema_meta (
              component TEXT PRIMARY KEY,
              schema_version INTEGER NOT NULL,
              migrated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS artifacts (
              artifact_id TEXT PRIMARY KEY,
              artifact_kind TEXT NOT NULL,
              layer TEXT NOT NULL,
              path TEXT NOT NULL DEFAULT '',
              title TEXT NOT NULL DEFAULT '',
              domain TEXT NOT NULL DEFAULT '',
              content_hash TEXT NOT NULL DEFAULT '',
              lifecycle_state TEXT NOT NULL DEFAULT 'current',
              authority TEXT NOT NULL DEFAULT 'derived',
              metadata_json TEXT NOT NULL DEFAULT '{}',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_artifacts_path ON artifacts(path);
            CREATE INDEX IF NOT EXISTS idx_artifacts_kind_state ON artifacts(artifact_kind, lifecycle_state);

            CREATE TABLE IF NOT EXISTS relationships (
              relationship_id TEXT PRIMARY KEY,
              source_artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id) ON DELETE CASCADE,
              target_artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id) ON DELETE CASCADE,
              relationship_type TEXT NOT NULL,
              source_hash TEXT NOT NULL DEFAULT '',
              target_hash TEXT NOT NULL DEFAULT '',
              method TEXT NOT NULL,
              method_version TEXT NOT NULL,
              model_version TEXT NOT NULL DEFAULT '',
              prompt_version TEXT NOT NULL DEFAULT '',
              confidence REAL,
              state TEXT NOT NULL,
              relationship_hash TEXT NOT NULL,
              invalidation_reason TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_artifact_id, state);
            CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_artifact_id, state);
            CREATE INDEX IF NOT EXISTS idx_relationships_type_state ON relationships(relationship_type, state);

            CREATE TABLE IF NOT EXISTS evidence_anchors (
              evidence_id TEXT PRIMARY KEY,
              relationship_id TEXT NOT NULL REFERENCES relationships(relationship_id) ON DELETE CASCADE,
              artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id) ON DELETE CASCADE,
              selector_type TEXT NOT NULL,
              selector_value TEXT NOT NULL,
              excerpt TEXT NOT NULL DEFAULT '',
              excerpt_sha256 TEXT NOT NULL DEFAULT '',
              source_hash TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_evidence_relationship ON evidence_anchors(relationship_id);

            CREATE TABLE IF NOT EXISTS relationship_reviews (
              review_id TEXT PRIMARY KEY,
              relationship_id TEXT NOT NULL REFERENCES relationships(relationship_id) ON DELETE CASCADE,
              relationship_hash TEXT NOT NULL,
              reviewer TEXT NOT NULL,
              verdict TEXT NOT NULL,
              note TEXT NOT NULL DEFAULT '',
              reviewed_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_reviews_relationship ON relationship_reviews(relationship_id, reviewed_at);

            CREATE TABLE IF NOT EXISTS dependency_edges (
              dependent_artifact_id TEXT NOT NULL,
              dependency_artifact_id TEXT NOT NULL,
              dependency_kind TEXT NOT NULL,
              dependency_hash TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL,
              PRIMARY KEY (dependent_artifact_id, dependency_artifact_id, dependency_kind)
            );
            CREATE INDEX IF NOT EXISTS idx_dependency_reverse ON dependency_edges(dependency_artifact_id, dependency_kind);

            CREATE TABLE IF NOT EXISTS invalidation_records (
              invalidation_id TEXT PRIMARY KEY,
              artifact_id TEXT NOT NULL,
              dependency_artifact_id TEXT NOT NULL,
              previous_hash TEXT NOT NULL DEFAULT '',
              current_hash TEXT NOT NULL DEFAULT '',
              reason TEXT NOT NULL,
              journal_sequence INTEGER,
              invalidated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_invalidation_artifact ON invalidation_records(artifact_id, invalidated_at);
            """
        )
        row = conn.execute(
            "SELECT schema_version FROM derived_schema_meta WHERE component = ?", (SCHEMA_COMPONENT,)
        ).fetchone()
        found = int(row[0]) if row else 0
        if found > RELATIONSHIP_SCHEMA_VERSION:
            raise RelationshipValidationError(
                f"relationship schema_version {found} is newer than this MirrorArc supports"
            )
        conn.execute(
            "INSERT INTO derived_schema_meta(component, schema_version, migrated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(component) DO UPDATE SET schema_version=excluded.schema_version, migrated_at=excluded.migrated_at",
            (SCHEMA_COMPONENT, RELATIONSHIP_SCHEMA_VERSION, utc_now()),
        )
        conn.commit()

    def upsert_artifact(self, artifact: dict[str, Any], *, conn: sqlite3.Connection | None = None) -> None:
        own = conn is None
        active = conn or self.connect()
        now = utc_now()
        artifact_id = str(artifact.get("artifact_id", "") or "").strip()
        if not artifact_id:
            raise RelationshipValidationError("artifact_id is required")
        metadata = artifact.get("metadata", {})
        if not isinstance(metadata, dict):
            raise RelationshipValidationError("artifact metadata must be a mapping")
        active.execute(
            """
            INSERT INTO artifacts(
              artifact_id, artifact_kind, layer, path, title, domain, content_hash,
              lifecycle_state, authority, metadata_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(artifact_id) DO UPDATE SET
              artifact_kind=excluded.artifact_kind, layer=excluded.layer, path=excluded.path,
              title=excluded.title, domain=excluded.domain, content_hash=excluded.content_hash,
              lifecycle_state=excluded.lifecycle_state, authority=excluded.authority,
              metadata_json=excluded.metadata_json, updated_at=excluded.updated_at
            """,
            (
                artifact_id, str(artifact.get("artifact_kind", "record")), str(artifact.get("layer", "L0")),
                str(artifact.get("path", "") or ""), str(artifact.get("title", "") or ""),
                str(artifact.get("domain", "") or ""), str(artifact.get("content_hash", "") or ""),
                str(artifact.get("lifecycle_state", "current") or "current"),
                str(artifact.get("authority", "authoritative") or "authoritative"),
                canonical_json(metadata), now, now,
            ),
        )
        if own:
            active.commit()
            active.close()

    def put_relationship(
        self,
        *,
        source_artifact_id: str,
        target_artifact_id: str,
        relationship_type: str,
        method: str,
        method_version: str,
        state: str,
        evidence: Iterable[EvidenceAnchor] = (),
        source_hash: str = "",
        target_hash: str = "",
        confidence: float | None = None,
        model_version: str = "",
        prompt_version: str = "",
        conn: sqlite3.Connection | None = None,
    ) -> str:
        rel_type = validate_relationship_type(relationship_type)
        rel_state = validate_state(state)
        method_value = method.strip()
        if not method_value or not method_version.strip():
            raise RelationshipValidationError("method and method_version are required")
        anchors = [anchor.validate() for anchor in evidence]
        if rel_type not in DETERMINISTIC_TYPES and not anchors:
            raise RelationshipValidationError("semantic relationships require at least one evidence anchor")
        if rel_type not in DETERMINISTIC_TYPES and rel_state == "accepted":
            raise RelationshipValidationError("semantic relationships must be proposed before review acceptance")
        if confidence is not None and not 0 <= confidence <= 1:
            raise RelationshipValidationError("confidence must be between 0 and 1")
        own = conn is None
        active = conn or self.connect()
        for artifact_id in (source_artifact_id, target_artifact_id):
            if active.execute("SELECT 1 FROM artifacts WHERE artifact_id = ?", (artifact_id,)).fetchone() is None:
                raise RelationshipValidationError(f"unknown artifact_id: {artifact_id}")
        rel_id = relationship_id(source_artifact_id, rel_type, target_artifact_id, method_value, method_version)
        now = utc_now()
        hash_payload = {
            "source_artifact_id": source_artifact_id,
            "target_artifact_id": target_artifact_id,
            "relationship_type": rel_type,
            "source_hash": source_hash,
            "target_hash": target_hash,
            "method": method_value,
            "method_version": method_version,
            "model_version": model_version,
            "prompt_version": prompt_version,
            "confidence": confidence,
            "evidence": [
                {
                    "artifact_id": anchor.artifact_id,
                    "selector_type": anchor.selector_type,
                    "selector_value": anchor.selector_value,
                    "source_hash": anchor.source_hash,
                    "excerpt_sha256": hashlib.sha256(anchor.excerpt.encode("utf-8")).hexdigest() if anchor.excerpt else "",
                }
                for anchor in anchors
            ],
        }
        rel_hash = hashlib.sha256(canonical_json(hash_payload).encode("utf-8")).hexdigest()
        active.execute(
            """
            INSERT INTO relationships(
              relationship_id, source_artifact_id, target_artifact_id, relationship_type,
              source_hash, target_hash, method, method_version, model_version, prompt_version,
              confidence, state, relationship_hash, invalidation_reason, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', ?, ?)
            ON CONFLICT(relationship_id) DO UPDATE SET
              source_hash=excluded.source_hash, target_hash=excluded.target_hash,
              model_version=excluded.model_version, prompt_version=excluded.prompt_version,
              confidence=excluded.confidence, relationship_hash=excluded.relationship_hash,
              state=CASE
                WHEN relationships.relationship_hash=excluded.relationship_hash
                 AND relationships.state IN ('accepted','rejected','invalidated') THEN relationships.state
                ELSE excluded.state
              END,
              invalidation_reason=CASE
                WHEN relationships.relationship_hash=excluded.relationship_hash THEN relationships.invalidation_reason
                ELSE ''
              END,
              updated_at=excluded.updated_at
            """,
            (
                rel_id, source_artifact_id, target_artifact_id, rel_type, source_hash, target_hash,
                method_value, method_version, model_version, prompt_version, confidence, rel_state,
                rel_hash, now, now,
            ),
        )
        active.execute("DELETE FROM evidence_anchors WHERE relationship_id = ?", (rel_id,))
        for anchor in anchors:
            if active.execute("SELECT 1 FROM artifacts WHERE artifact_id = ?", (anchor.artifact_id,)).fetchone() is None:
                raise RelationshipValidationError(f"unknown evidence artifact_id: {anchor.artifact_id}")
            ev_id = evidence_id(rel_id, anchor.artifact_id, anchor.selector_type, anchor.selector_value)
            excerpt = bounded_evidence(anchor.excerpt)
            active.execute(
                """
                INSERT INTO evidence_anchors(
                  evidence_id, relationship_id, artifact_id, selector_type, selector_value,
                  excerpt, excerpt_sha256, source_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(evidence_id) DO UPDATE SET excerpt=excluded.excerpt,
                  excerpt_sha256=excluded.excerpt_sha256, source_hash=excluded.source_hash
                """,
                (
                    ev_id, rel_id, anchor.artifact_id, anchor.selector_type, anchor.selector_value,
                    excerpt, hashlib.sha256(excerpt.encode("utf-8")).hexdigest() if excerpt else "",
                    anchor.source_hash, now,
                ),
            )
        if own:
            active.commit()
            active.close()
        return rel_id

    def review_relationship(self, relationship: str, *, reviewer: str, verdict: str, note: str = "") -> dict[str, Any]:
        reviewer_value = reviewer.strip()
        normalized_verdict = verdict.strip().lower()
        if not reviewer_value:
            raise RelationshipValidationError("reviewer is required")
        if normalized_verdict not in REVIEW_VERDICTS:
            raise RelationshipValidationError("verdict must be accepted or rejected")
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM relationships WHERE relationship_id = ?", (relationship,)).fetchone()
            if row is None:
                raise RelationshipValidationError(f"unknown relationship_id: {relationship}")
            if row["method"] == "deterministic":
                raise RelationshipValidationError("deterministic relationships do not require semantic review")
            if normalized_verdict == "accepted":
                count = conn.execute(
                    "SELECT COUNT(*) FROM evidence_anchors WHERE relationship_id = ?", (relationship,)
                ).fetchone()[0]
                if not count:
                    raise RelationshipValidationError("accepted semantic relationship requires evidence")
            now = utc_now()
            review_id = stable_id("review", relationship, str(row["relationship_hash"]), reviewer_value, normalized_verdict)
            conn.execute(
                "INSERT OR REPLACE INTO relationship_reviews(review_id, relationship_id, relationship_hash, reviewer, verdict, note, reviewed_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (review_id, relationship, row["relationship_hash"], reviewer_value, normalized_verdict, note.strip(), now),
            )
            conn.execute(
                "UPDATE relationships SET state = ?, invalidation_reason = '', updated_at = ? WHERE relationship_id = ?",
                (normalized_verdict, now, relationship),
            )
        return {"relationship_id": relationship, "state": normalized_verdict, "review_id": review_id}

    def invalidate_relationship(
        self,
        relationship: str,
        *,
        dependency_artifact_id: str,
        previous_hash: str,
        current_hash: str,
        reason: str,
        journal_sequence: int | None = None,
    ) -> dict[str, Any]:
        reason_value = reason.strip()
        if not reason_value:
            raise RelationshipValidationError("invalidation reason is required")
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM relationships WHERE relationship_id = ?", (relationship,)).fetchone()
            if row is None:
                raise RelationshipValidationError(f"unknown relationship_id: {relationship}")
            now = utc_now()
            invalidation_id = stable_id(
                "inv", relationship, dependency_artifact_id, previous_hash, current_hash,
                str(journal_sequence or 0), reason_value,
            )
            conn.execute(
                "UPDATE relationships SET state='invalidated', invalidation_reason=?, updated_at=? WHERE relationship_id=?",
                (reason_value, now, relationship),
            )
            conn.execute(
                "INSERT OR IGNORE INTO invalidation_records(invalidation_id, artifact_id, dependency_artifact_id, previous_hash, current_hash, reason, journal_sequence, invalidated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    invalidation_id, relationship, dependency_artifact_id, previous_hash, current_hash,
                    reason_value, journal_sequence, now,
                ),
            )
        return {"relationship_id": relationship, "state": "invalidated", "invalidation_id": invalidation_id}

    def replace_deterministic(self, artifacts: list[dict[str, Any]], relationships: list[dict[str, Any]]) -> dict[str, Any]:
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            deterministic_ids = [
                str(row[0]) for row in conn.execute(
                    "SELECT relationship_id FROM relationships WHERE method = 'deterministic'"
                ).fetchall()
            ]
            if deterministic_ids:
                conn.executemany("DELETE FROM relationships WHERE relationship_id = ?", [(value,) for value in deterministic_ids])
            for row in conn.execute("SELECT artifact_id, metadata_json FROM artifacts").fetchall():
                metadata = json.loads(str(row["metadata_json"]) or "{}")
                if metadata.get("deterministic_refresh") is True:
                    metadata["deterministic_refresh"] = False
                    conn.execute(
                        "UPDATE artifacts SET metadata_json = ?, updated_at = ? WHERE artifact_id = ?",
                        (canonical_json(metadata), utc_now(), row["artifact_id"]),
                    )
            conn.execute("DELETE FROM dependency_edges WHERE dependency_kind = 'deterministic'")
            for artifact in artifacts:
                payload = dict(artifact)
                metadata = dict(payload.get("metadata", {}))
                metadata["deterministic_refresh"] = True
                payload["metadata"] = metadata
                self.upsert_artifact(payload, conn=conn)
            for relationship in relationships:
                rel_id = self.put_relationship(conn=conn, **relationship)
                if relationship["relationship_type"] in {"DERIVED_FROM", "DEPENDS_ON", "REVIEW_DEPENDS_ON", "IN_CONTEXT"}:
                    conn.execute(
                        "INSERT OR REPLACE INTO dependency_edges(dependent_artifact_id, dependency_artifact_id, dependency_kind, dependency_hash, created_at) "
                        "VALUES (?, ?, 'deterministic', ?, ?)",
                        (
                            relationship["source_artifact_id"], relationship["target_artifact_id"],
                            relationship.get("target_hash", ""), utc_now(),
                        ),
                    )
        return {
            "artifacts": len(artifacts),
            "relationships": len(relationships),
            "fingerprint": self.deterministic_fingerprint(),
        }

    def replace_deterministic_for_artifacts(
        self,
        owned_artifact_ids: set[str],
        artifacts: list[dict[str, Any]],
        relationships: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Replace deterministic edges originating in one bounded affected subgraph."""
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            if owned_artifact_ids:
                placeholders = ",".join("?" for _ in owned_artifact_ids)
                conn.execute(
                    f"DELETE FROM relationships WHERE method='deterministic' AND source_artifact_id IN ({placeholders})",
                    tuple(sorted(owned_artifact_ids)),
                )
                conn.execute(
                    f"DELETE FROM dependency_edges WHERE dependency_kind='deterministic' AND dependent_artifact_id IN ({placeholders})",
                    tuple(sorted(owned_artifact_ids)),
                )
            for artifact in artifacts:
                payload = dict(artifact)
                metadata = dict(payload.get("metadata", {}))
                metadata["deterministic_refresh"] = True
                payload["metadata"] = metadata
                self.upsert_artifact(payload, conn=conn)
            for relationship in relationships:
                self.put_relationship(conn=conn, **relationship)
                if relationship["relationship_type"] in {"DERIVED_FROM", "DEPENDS_ON", "REVIEW_DEPENDS_ON", "IN_CONTEXT"}:
                    conn.execute(
                        "INSERT OR REPLACE INTO dependency_edges(dependent_artifact_id, dependency_artifact_id, dependency_kind, dependency_hash, created_at) "
                        "VALUES (?, ?, 'deterministic', ?, ?)",
                        (
                            relationship["source_artifact_id"], relationship["target_artifact_id"],
                            relationship.get("target_hash", ""), utc_now(),
                        ),
                    )
        return {"artifacts": len(artifacts), "relationships": len(relationships)}

    def affected_dependents(
        self,
        dependency_artifact_ids: set[str],
        *,
        max_depth: int = 16,
        max_nodes: int = 1000,
    ) -> dict[str, Any]:
        """Return a cycle-safe, bounded reverse dependency traversal."""
        if max_depth < 0 or max_nodes < 1:
            raise RelationshipValidationError("dependency traversal bounds must be positive")
        visited = set(dependency_artifact_ids)
        frontier = set(dependency_artifact_ids)
        levels: list[list[str]] = []
        truncated = False
        with self.connect() as conn:
            for _depth in range(max_depth):
                if not frontier:
                    break
                placeholders = ",".join("?" for _ in frontier)
                rows = conn.execute(
                    f"SELECT DISTINCT dependent_artifact_id FROM dependency_edges WHERE dependency_artifact_id IN ({placeholders}) ORDER BY dependent_artifact_id",
                    tuple(sorted(frontier)),
                ).fetchall()
                next_level = [str(row[0]) for row in rows if str(row[0]) not in visited]
                remaining = max_nodes - len(visited)
                if len(next_level) > remaining:
                    next_level = next_level[: max(remaining, 0)]
                    truncated = True
                if not next_level:
                    break
                levels.append(next_level)
                visited.update(next_level)
                frontier = set(next_level)
                if len(visited) >= max_nodes:
                    truncated = True
                    break
            else:
                if frontier:
                    truncated = True
        return {
            "roots": sorted(dependency_artifact_ids),
            "affected": sorted(visited - dependency_artifact_ids),
            "levels": levels,
            "visited": len(visited),
            "truncated": truncated,
            "max_depth": max_depth,
            "max_nodes": max_nodes,
        }

    def deterministic_fingerprint(self) -> str:
        export = self.export(current_only=False)
        payload = {
            "artifacts": [
                {key: item[key] for key in ("artifact_id", "artifact_kind", "layer", "path", "domain", "content_hash", "lifecycle_state", "authority")}
                for item in export["artifacts"]
                if item.get("metadata", {}).get("deterministic_refresh") is True
            ],
            "relationships": [
                {key: item[key] for key in (
                    "relationship_id", "source_artifact_id", "target_artifact_id", "relationship_type",
                    "source_hash", "target_hash", "method", "method_version", "state", "relationship_hash",
                )}
                for item in export["relationships"] if item["method"] == "deterministic"
            ],
        }
        return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()

    def status(self) -> dict[str, Any]:
        with self.connect() as conn:
            artifact_counts = {str(row[0]): int(row[1]) for row in conn.execute(
                "SELECT layer, COUNT(*) FROM artifacts GROUP BY layer ORDER BY layer"
            )}
            type_counts = {str(row[0]): int(row[1]) for row in conn.execute(
                "SELECT relationship_type, COUNT(*) FROM relationships GROUP BY relationship_type ORDER BY relationship_type"
            )}
            state_counts = {str(row[0]): int(row[1]) for row in conn.execute(
                "SELECT state, COUNT(*) FROM relationships GROUP BY state ORDER BY state"
            )}
            evidence_count = int(conn.execute("SELECT COUNT(*) FROM evidence_anchors").fetchone()[0])
            review_count = int(conn.execute("SELECT COUNT(*) FROM relationship_reviews").fetchone()[0])
            dependency_count = int(conn.execute("SELECT COUNT(*) FROM dependency_edges").fetchone()[0])
            invalidation_count = int(conn.execute("SELECT COUNT(*) FROM invalidation_records").fetchone()[0])
        return {
            "schema_version": RELATIONSHIP_SCHEMA_VERSION,
            "database": str(self.path),
            "artifacts": {"total": sum(artifact_counts.values()), "by_layer": artifact_counts},
            "relationships": {
                "total": sum(state_counts.values()), "by_type": type_counts, "by_state": state_counts,
                "current": sum(count for state, count in state_counts.items() if state not in {"rejected", "invalidated"}),
            },
            "evidence_anchors": evidence_count,
            "reviews": review_count,
            "dependency_edges": dependency_count,
            "invalidations": invalidation_count,
            "deterministic_fingerprint": self.deterministic_fingerprint(),
        }

    def export(self, *, current_only: bool = False) -> dict[str, Any]:
        with self.connect() as conn:
            artifacts = [dict(row) for row in conn.execute("SELECT * FROM artifacts ORDER BY artifact_id")]
            query = "SELECT * FROM relationships"
            if current_only:
                query += " WHERE state NOT IN ('rejected','invalidated')"
            relationships = [dict(row) for row in conn.execute(query + " ORDER BY relationship_id")]
            evidence = [dict(row) for row in conn.execute("SELECT * FROM evidence_anchors ORDER BY evidence_id")]
            reviews = [dict(row) for row in conn.execute("SELECT * FROM relationship_reviews ORDER BY review_id")]
        for artifact in artifacts:
            artifact["metadata"] = json.loads(artifact.pop("metadata_json"))
            artifact.pop("created_at", None)
            artifact.pop("updated_at", None)
        for relationship in relationships:
            relationship.pop("created_at", None)
            relationship.pop("updated_at", None)
            relationship["evidence"] = [item for item in evidence if item["relationship_id"] == relationship["relationship_id"]]
            relationship["reviews"] = [item for item in reviews if item["relationship_id"] == relationship["relationship_id"]]
        return {
            "schema_version": RELATIONSHIP_SCHEMA_VERSION,
            "artifacts": artifacts,
            "relationships": relationships,
        }
