# SPDX-License-Identifier: AGPL-3.0-or-later
"""Versioned L2 view metadata and lifecycle repository."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

import yaml

from mirrorarc.relationships.model import EvidenceAnchor
from mirrorarc.relationships.store import RelationshipStore, utc_now

VIEW_SCHEMA_VERSION = 1
COMPONENT = "knowledge_views"
VIEW_STATES = {"generated", "reviewed", "stale", "superseded", "failed"}
PERSISTED_ROOT = Path("_meta/knowledge-views")
_CITATION_PATTERN = re.compile(
    r"- Source: `(?P<source>[^`]+)`\n"
    r"- Readable evidence: `(?P<readable>[^`]+)`\n"
    r"- SHA-256/state hash: `(?P<source_hash>[0-9a-f]{64})`"
)


class KnowledgeViewError(ValueError):
    """Raised for invalid L2 lifecycle operations."""


class KnowledgeViewStore:
    def __init__(self, root: Path):
        self.root = root.expanduser().resolve()
        self.relationships = RelationshipStore(self.root)

    def connect(self) -> sqlite3.Connection:
        conn = self.relationships.connect()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS knowledge_views (
              view_id TEXT PRIMARY KEY,
              lens_id TEXT NOT NULL,
              definition_hash TEXT NOT NULL,
              dependency_hash TEXT NOT NULL,
              state TEXT NOT NULL,
              version INTEGER NOT NULL,
              output_path TEXT NOT NULL,
              output_hash TEXT NOT NULL,
              citations_json TEXT NOT NULL DEFAULT '[]',
              generation_method TEXT NOT NULL,
              model_version TEXT NOT NULL DEFAULT '',
              prompt_version TEXT NOT NULL DEFAULT '',
              persistence TEXT NOT NULL DEFAULT 'ephemeral',
              pinned INTEGER NOT NULL DEFAULT 0,
              refresh_queued INTEGER NOT NULL DEFAULT 0,
              reviewer TEXT NOT NULL DEFAULT '',
              reviewed_at TEXT NOT NULL DEFAULT '',
              stale_reason TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_views_lens_state ON knowledge_views(lens_id, state, version);

            CREATE TABLE IF NOT EXISTS knowledge_view_versions (
              view_id TEXT NOT NULL REFERENCES knowledge_views(view_id) ON DELETE CASCADE,
              version INTEGER NOT NULL,
              dependency_hash TEXT NOT NULL,
              output_hash TEXT NOT NULL,
              output_path TEXT NOT NULL,
              state TEXT NOT NULL,
              created_at TEXT NOT NULL,
              PRIMARY KEY(view_id, version)
            );
            """
        )
        row = conn.execute(
            "SELECT schema_version FROM derived_schema_meta WHERE component=?", (COMPONENT,)
        ).fetchone()
        found = int(row[0]) if row else 0
        if found > VIEW_SCHEMA_VERSION:
            conn.close()
            raise KnowledgeViewError(f"knowledge-view schema_version {found} is newer than supported")
        conn.execute(
            "INSERT INTO derived_schema_meta(component,schema_version,migrated_at) VALUES (?,?,?) "
            "ON CONFLICT(component) DO UPDATE SET schema_version=excluded.schema_version,migrated_at=excluded.migrated_at",
            (COMPONENT, VIEW_SCHEMA_VERSION, utc_now()),
        )
        conn.commit()
        return conn

    @staticmethod
    def _frontmatter_and_body(path: Path) -> tuple[dict[str, Any], str]:
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            raise KnowledgeViewError(f"persisted view has no frontmatter: {path}")
        end = text.find("\n---", 3)
        if end == -1:
            raise KnowledgeViewError(f"persisted view has unterminated frontmatter: {path}")
        try:
            value = yaml.safe_load(text[3:end].lstrip("\n")) or {}
        except yaml.YAMLError as exc:
            raise KnowledgeViewError(f"persisted view frontmatter is invalid: {path}: {exc}") from exc
        if not isinstance(value, dict):
            raise KnowledgeViewError(f"persisted view frontmatter must be a mapping: {path}")
        return value, text[end + 4:].lstrip()

    def _recover_citations(self, metadata: dict[str, Any], body: str) -> list[dict[str, Any]]:
        declared = metadata.get("citations", [])
        if isinstance(declared, list) and declared and all(isinstance(item, dict) for item in declared):
            return [dict(item) for item in declared]

        graph = self.relationships.export(current_only=True)
        artifacts = {item["artifact_id"]: item for item in graph["artifacts"]}
        by_path = {
            str(item.get("path", "")): item
            for item in graph["artifacts"]
            if item.get("artifact_kind") in {"source", "native-source", "repository"}
        }
        projections = {
            item["target_artifact_id"]: artifacts.get(item["source_artifact_id"])
            for item in graph["relationships"]
            if item["relationship_type"] == "MIRRORS"
        }
        citations: list[dict[str, Any]] = []
        for match in _CITATION_PATTERN.finditer(body):
            source_path = match.group("source")
            artifact = by_path.get(source_path)
            if artifact is None:
                continue
            projection = projections.get(artifact["artifact_id"]) or {}
            citations.append({
                "artifact_id": artifact["artifact_id"],
                "source_path": source_path,
                "readable_path": match.group("readable"),
                "source_hash": match.group("source_hash"),
                "projection_id": str(projection.get("artifact_id", "") or ""),
                "projection_hash": str(projection.get("content_hash", "") or ""),
            })
        return citations

    def _import_missing_persisted(self) -> list[str]:
        from mirrorarc.knowledge_views.definitions import get_lens

        candidates: list[tuple[Path, dict[str, Any], str, str]] = []
        for persistence, state in (("reviewed", "reviewed"), ("pinned", "generated")):
            folder = self.root / PERSISTED_ROOT / persistence
            if not folder.is_dir() or folder.is_symlink():
                continue
            for path in sorted(folder.glob("*.md")):
                if path.is_symlink():
                    continue
                metadata, body = self._frontmatter_and_body(path)
                view_id = str(metadata.get("view_id", "") or "")
                if not view_id or path.stem != view_id:
                    raise KnowledgeViewError(f"persisted view identity does not match its filename: {path}")
                candidates.append((path, metadata, body, state))

        versions: dict[str, int] = {}
        imported: list[str] = []
        candidates.sort(key=lambda item: (
            str(item[1].get("lens_id", "")),
            str(item[1].get("reviewed_at", "")),
            str(item[1].get("view_id", "")),
        ))
        for path, metadata, body, state in candidates:
            view_id = str(metadata["view_id"])
            if self.get(view_id) is not None:
                continue
            lens_id = str(metadata.get("lens_id", "") or "")
            if not lens_id:
                raise KnowledgeViewError(f"persisted view has no lens_id: {path}")
            lens = get_lens(self.root, lens_id)
            declared_body_hash = str(metadata.get("output_hash", "") or "")
            actual_body_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
            if declared_body_hash and declared_body_hash != actual_body_hash:
                raise KnowledgeViewError(f"persisted view body hash differs from frontmatter: {path}")
            versions[lens_id] = versions.get(lens_id, 0) + 1
            version = int(metadata.get("version") or versions[lens_id])
            citations = self._recover_citations(metadata, body)
            output_rel = path.relative_to(self.root).as_posix()
            persisted_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            self.register(
                view_id=view_id,
                lens_id=lens_id,
                definition_hash=str(metadata.get("definition_hash", "") or lens["definition_hash"]),
                dependency_hash=str(metadata.get("dependency_hash", "") or ""),
                state=state,
                version=version,
                output_path=output_rel,
                output_hash=persisted_hash,
                citations=citations,
                generation_method=str(metadata.get("generation_method", "") or "deterministic"),
                model_version=str(metadata.get("model_version", "") or ""),
                prompt_version=str(metadata.get("prompt_version", "") or ""),
                persistence=path.parent.name,
            )
            with self.connect() as conn:
                now = utc_now()
                reviewer = str(metadata.get("reviewer", "") or "")
                reviewed_at = str(metadata.get("reviewed_at", "") or "")
                conn.execute(
                    "UPDATE knowledge_views SET state=?,persistence=?,pinned=1,reviewer=?,reviewed_at=?,updated_at=? WHERE view_id=?",
                    (state, path.parent.name, reviewer, reviewed_at, now, view_id),
                )
                conn.execute(
                    "UPDATE knowledge_view_versions SET state=?,output_path=?,output_hash=? WHERE view_id=?",
                    (state, output_rel, persisted_hash, view_id),
                )
            imported.append(view_id)
        return imported

    def reconcile_persisted(self) -> dict[str, Any]:
        """Reattach governed view files and rebuild their bounded dependency edges."""
        imported = self._import_missing_persisted()
        restored: list[str] = []
        graph = self.relationships.export(current_only=True)
        known_artifacts = {item["artifact_id"] for item in graph["artifacts"]}
        for record in self.list():
            output_rel = Path(str(record["output_path"]))
            if output_rel.is_absolute() or ".." in output_rel.parts:
                continue
            output_path = self.root / output_rel
            if not output_path.is_file() or output_path.is_symlink():
                continue
            dependencies = [
                item for item in record["citations"]
                if str(item.get("artifact_id", "")) in known_artifacts
            ]
            artifact = {
                "artifact_id": record["view_id"],
                "artifact_kind": "knowledge-view",
                "layer": "L2",
                "path": output_rel.as_posix(),
                "title": record["lens_id"],
                "content_hash": record["output_hash"],
                "lifecycle_state": record["state"],
                "authority": "reviewed-derived" if record["state"] in {"reviewed", "stale"} else "derived",
                "metadata": {
                    "lens_id": record["lens_id"],
                    "definition_hash": record["definition_hash"],
                    "dependency_hash": record["dependency_hash"],
                    "version": record["version"],
                },
            }
            relations = [
                {
                    "source_artifact_id": record["view_id"],
                    "target_artifact_id": item["artifact_id"],
                    "relationship_type": "DEPENDS_ON",
                    "method": "deterministic",
                    "method_version": "knowledge-view:v1",
                    "state": "accepted",
                    "source_hash": record["output_hash"],
                    "target_hash": str(item.get("source_hash", "") or item.get("content_hash", "") or ""),
                    "evidence": [EvidenceAnchor(
                        record["view_id"], "citation", item["artifact_id"], record["output_hash"]
                    )],
                }
                for item in dependencies
            ]
            self.relationships.replace_deterministic_for_artifacts(
                {record["view_id"]}, [artifact], relations
            )
            with self.relationships.connect() as conn:
                conn.execute(
                    "DELETE FROM dependency_edges WHERE dependent_artifact_id=? AND dependency_kind='view-input'",
                    (record["view_id"],),
                )
                conn.executemany(
                    "INSERT OR REPLACE INTO dependency_edges(dependent_artifact_id,dependency_artifact_id,dependency_kind,dependency_hash,created_at) VALUES (?,?,?,?,?)",
                    [
                        (
                            record["view_id"], item["artifact_id"], "view-input",
                            str(item.get("source_hash", "") or item.get("content_hash", "") or ""), utc_now(),
                        )
                        for item in dependencies
                    ],
                )
            restored.append(record["view_id"])
        return {"imported": imported, "restored": restored}

    def next_version(self, lens_id: str) -> int:
        with self.connect() as conn:
            row = conn.execute("SELECT MAX(version) FROM knowledge_views WHERE lens_id=?", (lens_id,)).fetchone()
        return int(row[0] or 0) + 1

    def get(self, view_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM knowledge_views WHERE view_id=?", (view_id,)).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["citations"] = json.loads(result.pop("citations_json"))
        return result

    def find_by_dependency(self, lens_id: str, definition_hash: str, dependency_hash: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM knowledge_views WHERE lens_id=? AND definition_hash=? AND dependency_hash=? ORDER BY version DESC LIMIT 1",
                (lens_id, definition_hash, dependency_hash),
            ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["citations"] = json.loads(result.pop("citations_json"))
        return result

    def register(
        self,
        *,
        view_id: str,
        lens_id: str,
        definition_hash: str,
        dependency_hash: str,
        state: str,
        version: int,
        output_path: str,
        output_hash: str,
        citations: list[dict[str, Any]],
        generation_method: str,
        model_version: str = "",
        prompt_version: str = "",
        persistence: str = "ephemeral",
    ) -> dict[str, Any]:
        if state not in VIEW_STATES:
            raise KnowledgeViewError(f"invalid view state: {state}")
        now = utc_now()
        with self.connect() as conn:
            existing = conn.execute("SELECT created_at FROM knowledge_views WHERE view_id=?", (view_id,)).fetchone()
            created = str(existing[0]) if existing else now
            conn.execute(
                """
                INSERT INTO knowledge_views(
                  view_id,lens_id,definition_hash,dependency_hash,state,version,output_path,output_hash,
                  citations_json,generation_method,model_version,prompt_version,persistence,
                  pinned,refresh_queued,created_at,updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,0,0,?,?)
                ON CONFLICT(view_id) DO UPDATE SET
                  output_path=excluded.output_path,output_hash=excluded.output_hash,
                  citations_json=excluded.citations_json,generation_method=excluded.generation_method,
                  model_version=excluded.model_version,prompt_version=excluded.prompt_version,
                  updated_at=excluded.updated_at
                """,
                (
                    view_id,lens_id,definition_hash,dependency_hash,state,version,output_path,output_hash,
                    json.dumps(citations, sort_keys=True, separators=(",", ":")),generation_method,
                    model_version,prompt_version,persistence,created,now,
                ),
            )
            conn.execute(
                "INSERT OR IGNORE INTO knowledge_view_versions(view_id,version,dependency_hash,output_hash,output_path,state,created_at) VALUES (?,?,?,?,?,?,?)",
                (view_id,version,dependency_hash,output_hash,output_path,state,now),
            )
        return self.get(view_id) or {}

    def set_pinned(self, view_id: str, output_path: str, output_hash: str) -> dict[str, Any]:
        with self.connect() as conn:
            row = conn.execute("SELECT state FROM knowledge_views WHERE view_id=?", (view_id,)).fetchone()
            if row is None:
                raise KnowledgeViewError(f"unknown view_id: {view_id}")
            conn.execute(
                "UPDATE knowledge_views SET pinned=1,persistence='pinned',output_path=?,output_hash=?,updated_at=? WHERE view_id=?",
                (output_path,output_hash,utc_now(),view_id),
            )
            conn.execute("UPDATE knowledge_view_versions SET output_path=?,output_hash=? WHERE view_id=?", (output_path,output_hash,view_id))
        return self.get(view_id) or {}

    def supersede_generated(self, lens_id: str, current_view_id: str) -> int:
        with self.connect() as conn:
            cursor = conn.execute(
                "UPDATE knowledge_views SET state='superseded',refresh_queued=0,updated_at=? "
                "WHERE lens_id=? AND view_id<>? AND state='generated'",
                (utc_now(),lens_id,current_view_id),
            )
        return int(cursor.rowcount)

    def stale_reviewed_except(
        self,
        lens_id: str,
        definition_hash: str,
        dependency_hash: str,
        *,
        reason: str,
    ) -> list[str]:
        """Mark reviewed versions stale when the current lens or evidence snapshot differs."""
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT view_id FROM knowledge_views WHERE lens_id=? AND state='reviewed' "
                "AND (definition_hash<>? OR dependency_hash<>?) ORDER BY version",
                (lens_id, definition_hash, dependency_hash),
            ).fetchall()
            view_ids = [str(row[0]) for row in rows]
            if view_ids:
                now = utc_now()
                conn.executemany(
                    "UPDATE knowledge_views SET state='stale',refresh_queued=1,stale_reason=?,updated_at=? "
                    "WHERE view_id=?",
                    [(reason, now, view_id) for view_id in view_ids],
                )
                conn.executemany(
                    "UPDATE knowledge_view_versions SET state='stale' WHERE view_id=?",
                    [(view_id,) for view_id in view_ids],
                )
                conn.executemany(
                    "UPDATE artifacts SET lifecycle_state='stale',updated_at=? WHERE artifact_id=?",
                    [(now, view_id) for view_id in view_ids],
                )
        return view_ids

    def review(self, view_id: str, reviewer: str, output_path: str, output_hash: str) -> dict[str, Any]:
        reviewer_value = reviewer.strip()
        if not reviewer_value:
            raise KnowledgeViewError("reviewer is required")
        with self.connect() as conn:
            row = conn.execute("SELECT state FROM knowledge_views WHERE view_id=?", (view_id,)).fetchone()
            if row is None:
                raise KnowledgeViewError(f"unknown view_id: {view_id}")
            if str(row[0]) not in {"generated", "stale"}:
                raise KnowledgeViewError(f"view cannot be reviewed from state {row[0]}")
            now = utc_now()
            conn.execute(
                "UPDATE knowledge_views SET state='reviewed',persistence='reviewed',pinned=1,reviewer=?,reviewed_at=?,output_path=?,output_hash=?,refresh_queued=0,stale_reason='',updated_at=? WHERE view_id=?",
                (reviewer_value,now,output_path,output_hash,now,view_id),
            )
            conn.execute(
                "UPDATE knowledge_view_versions SET state='reviewed',output_path=?,output_hash=? WHERE view_id=?",
                (output_path,output_hash,view_id),
            )
        return self.get(view_id) or {}

    def list(self, *, lens_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM knowledge_views"
        params: tuple[Any, ...] = ()
        if lens_id:
            query += " WHERE lens_id=?"
            params = (lens_id,)
        query += " ORDER BY lens_id,version DESC"
        with self.connect() as conn:
            rows = [dict(row) for row in conn.execute(query, params)]
        for row in rows:
            row["citations"] = json.loads(row.pop("citations_json"))
        return rows

    def status(self) -> dict[str, Any]:
        with self.connect() as conn:
            by_state = {str(row[0]): int(row[1]) for row in conn.execute(
                "SELECT state,COUNT(*) FROM knowledge_views GROUP BY state ORDER BY state"
            )}
            persistent = int(conn.execute(
                "SELECT COUNT(*) FROM knowledge_views WHERE pinned=1 OR state='reviewed'"
            ).fetchone()[0])
            dependencies = int(conn.execute(
                "SELECT COUNT(*) FROM dependency_edges WHERE dependency_kind='view-input'"
            ).fetchone()[0])
        return {"schema_version": VIEW_SCHEMA_VERSION,"total":sum(by_state.values()),"by_state":by_state,"persistent":persistent,"dependencies":dependencies}
