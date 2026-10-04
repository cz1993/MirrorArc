# SPDX-License-Identifier: AGPL-3.0-or-later
"""Versioned local state for context definitions and immutable packs."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from mirrorarc.relationships.store import RelationshipStore, utc_now

CONTEXT_SCHEMA_VERSION = 1
COMPONENT = "context_assembly"


class ContextStoreError(ValueError):
    """Raised when context state is incompatible or incomplete."""


class ContextStore:
    def __init__(self, root: Path):
        self.root = root.expanduser().resolve()
        self.relationships = RelationshipStore(self.root)

    def connect(self) -> sqlite3.Connection:
        conn = self.relationships.connect()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS context_definitions (
              definition_id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              lens_id TEXT NOT NULL,
              purpose TEXT NOT NULL,
              selection_json TEXT NOT NULL,
              budgets_json TEXT NOT NULL,
              freshness_policy TEXT NOT NULL,
              permitted_types_json TEXT NOT NULL,
              sensitivity_policy TEXT NOT NULL,
              definition_hash TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS context_packs (
              context_id TEXT PRIMARY KEY,
              definition_id TEXT NOT NULL,
              mode TEXT NOT NULL,
              dependency_hash TEXT NOT NULL,
              output_path TEXT NOT NULL,
              output_hash TEXT NOT NULL,
              freshness_state TEXT NOT NULL,
              stale_reason TEXT NOT NULL DEFAULT '',
              selection_count INTEGER NOT NULL,
              included_count INTEGER NOT NULL,
              omissions_json TEXT NOT NULL DEFAULT '[]',
              warnings_json TEXT NOT NULL DEFAULT '[]',
              sensitivity TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_context_mode_state ON context_packs(mode, freshness_state);
            CREATE TABLE IF NOT EXISTS context_pack_items (
              context_id TEXT NOT NULL REFERENCES context_packs(context_id) ON DELETE CASCADE,
              artifact_id TEXT NOT NULL,
              source_hash TEXT NOT NULL,
              projection_hash TEXT NOT NULL DEFAULT '',
              view_version INTEGER,
              excerpt_hash TEXT NOT NULL DEFAULT '',
              PRIMARY KEY(context_id, artifact_id)
            );
            """
        )
        row = conn.execute(
            "SELECT schema_version FROM derived_schema_meta WHERE component=?", (COMPONENT,)
        ).fetchone()
        found = int(row[0]) if row else 0
        if found > CONTEXT_SCHEMA_VERSION:
            conn.close()
            raise ContextStoreError(f"context schema_version {found} is newer than supported")
        conn.execute(
            "INSERT INTO derived_schema_meta(component,schema_version,migrated_at) VALUES (?,?,?) "
            "ON CONFLICT(component) DO UPDATE SET schema_version=excluded.schema_version,migrated_at=excluded.migrated_at",
            (COMPONENT, CONTEXT_SCHEMA_VERSION, utc_now()),
        )
        conn.commit()
        return conn

    @staticmethod
    def _decode_definition(row: sqlite3.Row) -> dict[str, Any]:
        value = dict(row)
        for field in ("selection_json", "budgets_json", "permitted_types_json"):
            value[field.removesuffix("_json")] = json.loads(value.pop(field))
        return value

    @staticmethod
    def _decode_pack(row: sqlite3.Row) -> dict[str, Any]:
        value = dict(row)
        value["omissions"] = json.loads(value.pop("omissions_json"))
        value["warnings"] = json.loads(value.pop("warnings_json"))
        return value

    def put_definition(self, definition: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT created_at FROM context_definitions WHERE definition_id=?",
                (definition["definition_id"],),
            ).fetchone()
            created = str(existing[0]) if existing else now
            conn.execute(
                """
                INSERT INTO context_definitions(
                  definition_id,name,lens_id,purpose,selection_json,budgets_json,freshness_policy,
                  permitted_types_json,sensitivity_policy,definition_hash,created_at,updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(definition_id) DO UPDATE SET
                  name=excluded.name,lens_id=excluded.lens_id,purpose=excluded.purpose,
                  selection_json=excluded.selection_json,budgets_json=excluded.budgets_json,
                  freshness_policy=excluded.freshness_policy,
                  permitted_types_json=excluded.permitted_types_json,
                  sensitivity_policy=excluded.sensitivity_policy,
                  definition_hash=excluded.definition_hash,updated_at=excluded.updated_at
                """,
                (
                    definition["definition_id"], definition["name"], definition["lens_id"],
                    definition["purpose"], json.dumps(definition["selection"], sort_keys=True, separators=(",", ":")),
                    json.dumps(definition["budgets"], sort_keys=True, separators=(",", ":")),
                    definition["freshness_policy"],
                    json.dumps(definition["permitted_types"], sort_keys=True, separators=(",", ":")),
                    definition["sensitivity_policy"], definition["definition_hash"], created, now,
                ),
            )
        return self.get_definition(str(definition["definition_id"])) or {}

    def get_definition(self, definition_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM context_definitions WHERE definition_id=?", (definition_id,)
            ).fetchone()
        return self._decode_definition(row) if row else None

    def list_definitions(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM context_definitions ORDER BY name,definition_id").fetchall()
        return [self._decode_definition(row) for row in rows]

    def get_pack(self, context_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM context_packs WHERE context_id=?", (context_id,)).fetchone()
        return self._decode_pack(row) if row else None

    def put_pack(self, pack: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
        now = utc_now()
        with self.connect() as conn:
            existing = conn.execute(
                "SELECT created_at FROM context_packs WHERE context_id=?", (pack["context_id"],)
            ).fetchone()
            created = str(existing[0]) if existing else str(pack.get("created_at") or now)
            conn.execute(
                """
                INSERT INTO context_packs(
                  context_id,definition_id,mode,dependency_hash,output_path,output_hash,
                  freshness_state,stale_reason,selection_count,included_count,omissions_json,
                  warnings_json,sensitivity,created_at,updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(context_id) DO UPDATE SET
                  output_path=excluded.output_path,output_hash=excluded.output_hash,
                  freshness_state=excluded.freshness_state,stale_reason=excluded.stale_reason,
                  updated_at=excluded.updated_at
                """,
                (
                    pack["context_id"], pack["definition_id"], pack["mode"], pack["dependency_hash"],
                    pack["output_path"], pack["output_hash"], pack["freshness_state"],
                    pack.get("stale_reason", ""), pack["selection_count"], pack["included_count"],
                    json.dumps(pack["omissions"], sort_keys=True, separators=(",", ":")),
                    json.dumps(pack["warnings"], sort_keys=True, separators=(",", ":")),
                    pack["sensitivity"], created, now,
                ),
            )
            conn.execute("DELETE FROM context_pack_items WHERE context_id=?", (pack["context_id"],))
            conn.executemany(
                "INSERT INTO context_pack_items(context_id,artifact_id,source_hash,projection_hash,view_version,excerpt_hash) VALUES (?,?,?,?,?,?)",
                [
                    (
                        pack["context_id"], item["artifact_id"], item["source_hash"],
                        item.get("projection_hash", ""), item.get("view_version"),
                        item.get("excerpt_hash", ""),
                    )
                    for item in items
                ],
            )
        return self.get_pack(str(pack["context_id"])) or {}

    def pack_items(self, context_id: str) -> list[dict[str, Any]]:
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(
                "SELECT * FROM context_pack_items WHERE context_id=? ORDER BY artifact_id", (context_id,)
            )]

    def list_packs(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM context_packs ORDER BY created_at,context_id").fetchall()
        return [self._decode_pack(row) for row in rows]

    def status(self, context_id: str | None = None) -> dict[str, Any]:
        packs = [self.get_pack(context_id)] if context_id else self.list_packs()
        packs = [pack for pack in packs if pack]
        definitions = self.list_definitions()
        definitions_by_id = {item["definition_id"]: item for item in definitions}
        graph = self.relationships.export(current_only=True)
        hashes = {item["artifact_id"]: item["content_hash"] for item in graph["artifacts"]}
        for pack in packs:
            if pack["mode"] != "frozen":
                pack["newer_versions"] = []
                continue
            newer = [
                {"artifact_id": item["artifact_id"], "packed_hash": item["source_hash"], "current_hash": hashes.get(item["artifact_id"], "")}
                for item in self.pack_items(pack["context_id"])
                if hashes.get(item["artifact_id"], "") != item["source_hash"]
            ]
            pack["newer_versions"] = newer
            if newer:
                pack["freshness_state"] = "stale"
                pack["stale_reason"] = "newer source or view versions are available"
            definition = definitions_by_id.get(pack["definition_id"], {})
            selection = definition.get("selection", {}) if isinstance(definition, dict) else {}
            if isinstance(selection, dict) and selection.get('kind') == 'document-evidence':
                from mirrorarc.document_intelligence.service import source_record
                from mirrorarc.document_intelligence.adapter import DocumentIntelligenceError
                try:
                    source_record(self.root, selection['source_id'])
                except DocumentIntelligenceError:
                    pack['freshness_state'] = 'stale'
                    pack['stale_reason'] = 'PDF source changed, is missing, or is no longer eligible; refresh and review'
            if isinstance(selection, dict) and selection.get("kind") == "code-evidence":
                from mirrorarc.code_intelligence.service import status_report

                code_status = status_report(self.root, str(selection.get("repo_id", "") or ""))
                item = code_status["items"][0] if code_status["items"] else None
                packed_ids = {
                    value["artifact_id"] for value in self.pack_items(pack["context_id"])
                }
                analysis_summary = (item or {}).get("analysis")
                analysis_summary = analysis_summary if isinstance(analysis_summary, dict) else {}
                current_analysis_id = str(analysis_summary.get("analysis_id", "") or "")
                newer_code_analysis = bool(current_analysis_id and current_analysis_id not in packed_ids)
                if item and (
                    item["freshness_state"] not in {"current", "local-uncommitted"}
                    or newer_code_analysis
                ):
                    pack["freshness_state"] = "stale"
                    pack["stale_reason"] = (
                        "newer repository evidence is available"
                        if newer_code_analysis
                        else item["reason"] or "newer repository evidence is available"
                    )
                    pack["newer_versions"].append({
                        "artifact_id": item["repo_id"],
                        "packed_hash": pack["dependency_hash"],
                        "current_hash": current_analysis_id or item["freshness_state"],
                    })
        return {
            "schema_version": CONTEXT_SCHEMA_VERSION,
            "definitions": definitions,
            "packs": packs,
        }
