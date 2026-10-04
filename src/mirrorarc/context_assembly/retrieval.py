# SPDX-License-Identifier: AGPL-3.0-or-later
"""Disposable lexical task retrieval inside MirrorArc's existing state database."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

from mirrorarc.relationships.store import RelationshipStore

SCHEMA_VERSION = 1
MAX_CANDIDATES = 500
MAX_FILE_BYTES = 256 * 1024
MAX_INDEX_BYTES = 8 * 1024 * 1024
MAX_CHUNKS = 10000


def retrieve(root: Path, definition: dict[str, Any], candidates: list[dict[str, Any]], relations: list[dict[str, Any]]):
    from mirrorarc.context_assembly.builder import CACHE_ROOT, ContextAssemblyError, _safe_path, _write_atomic, TEXT_SUFFIXES, verified_readable

    query = str(definition['selection'].get('query', ''))
    words = re.findall(r'[^\W_]+', query, flags=re.UNICODE)[:32]
    if not words:
        raise ContextAssemblyError('task query must contain searchable words')
    match = ' OR '.join('"' + word.replace('"', '""') + '"' for word in words)
    exclusions = []
    eligible = []
    chunks = []
    byte_count = 0
    for index, item in enumerate(candidates):
        reason = ''
        if index >= MAX_CANDIDATES:
            reason = 'candidate_limit'
        elif item['artifact_kind'] not in {'source', 'native-source'}:
            reason = 'task_retrieval_requires_authoritative_text_or_L1'
        elif item['lifecycle_state'] not in {'current', 'clean', 'active'}:
            reason = 'not_current'
        path = _safe_path(root, item['readable_path']) if not reason else None
        if not reason and (path is None or path.suffix.lower() not in TEXT_SUFFIXES):
            reason = 'unavailable_or_unsupported_text'
        if not reason and (path.stat().st_size > MAX_FILE_BYTES or byte_count + path.stat().st_size > MAX_INDEX_BYTES):
            reason = 'index_byte_limit'
        if reason:
            exclusions.append({'artifact_id': item['artifact_id'], 'reason': reason})
            continue
        raw = path.read_bytes()
        byte_count += len(raw)
        expected = item['projection_hash'] or item['source_hash']
        if not verified_readable(root, item, raw):
            exclusions.append({'artifact_id': item['artifact_id'], 'reason': 'stale_content_hash; refresh sources first'})
            continue
        try:
            text = raw.decode('utf-8')
        except UnicodeDecodeError:
            exclusions.append({'artifact_id': item['artifact_id'], 'reason': 'unsupported_encoding'})
            continue
        lines = text.splitlines(keepends=True)
        start = 0
        if lines and lines[0].strip() == '---':
            for end in range(1, len(lines)):
                if lines[end].strip() == '---':
                    start = end + 1
                    break
        for offset in range(start, len(lines), 40):
            body = ''.join(lines[offset:offset + 40])
            heading = ' '.join(line.lstrip('#').strip() for line in lines[start:offset + 40] if line.startswith('#'))[-2000:]
            if len(chunks) >= MAX_CHUNKS:
                raise ContextAssemblyError('task retrieval chunk limit exceeded')
            chunks.append((item['artifact_id'], expected, offset + 1, min(offset + 40, len(lines)), heading, body))
        eligible.append(item)
    signature = hashlib.sha256(json.dumps(chunks, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
    try:
        with RelationshipStore(root).connect() as conn:
            # Probe FTS5 on the actual runtime, without loading extensions.
            conn.execute('CREATE VIRTUAL TABLE IF NOT EXISTS temp.fts5_probe USING fts5(value)')
            conn.execute('CREATE TABLE IF NOT EXISTS context_search_meta(version INTEGER, signature TEXT)')
            current = conn.execute('SELECT version, signature FROM context_search_meta').fetchone()
            exists = conn.execute("SELECT 1 FROM sqlite_master WHERE name='context_search'").fetchone()
            if not exists or not current or tuple(current) != (SCHEMA_VERSION, signature):
                conn.execute('DROP TABLE IF EXISTS context_search')
                conn.execute('CREATE VIRTUAL TABLE context_search USING fts5(artifact_id UNINDEXED, content_hash UNINDEXED, start_line UNINDEXED, end_line UNINDEXED, heading, body, tokenize="unicode61")')
                conn.executemany('INSERT INTO context_search VALUES (?,?,?,?,?,?)', chunks)
                conn.execute('DELETE FROM context_search_meta')
                conn.execute('INSERT INTO context_search_meta VALUES (?,?)', (SCHEMA_VERSION, signature))
            rows = conn.execute('SELECT artifact_id, start_line, end_line, bm25(context_search,0,0,0,0,4,1) AS score FROM context_search WHERE context_search MATCH ? ORDER BY score, artifact_id, CAST(start_line AS INTEGER) LIMIT 500', (match,)).fetchall()
    except sqlite3.OperationalError as exc:
        raise ContextAssemblyError('Task retrieval requires SQLite FTS5; use explicit lens selection without --query or a Python runtime with FTS5. ' + str(exc)) from exc
    by_id = {item['artifact_id']: item for item in eligible}
    selected = []
    seen = set()
    for row in rows:
        identity = row['artifact_id']
        if identity in seen or identity not in by_id:
            continue
        seen.add(identity)
        selected.append({**by_id[identity], 'retrieval': {
            'reason': 'lexical-task-match', 'method': 'fts5-unicode61-bm25-heading4-body1-v1',
            'score': row['score'], 'freshness': 'hash-verified-current',
            'line_ranges': [{'start': int(row['start_line']), 'end': int(row['end_line'])}],
        }})
        if len(selected) >= definition['budgets']['max_files']:
            break
    # One hop only, bounded by remaining file capacity. The caller supplies only
    # accepted edges with matching endpoint hashes; no cached edge is authority.
    seeds = {item['artifact_id'] for item in selected}
    for relation in sorted(relations, key=lambda r: r['relationship_id']):
        if len(selected) >= definition['budgets']['max_files']:
            break
        if relation['relationship_type'] not in definition.get('relationship_types', definition['selection'].get('relationship_types', [])):
            continue
        a, b = relation['source_artifact_id'], relation['target_artifact_id']
        target = b if a in seeds else a if b in seeds else None
        if target not in by_id or target in seen:
            continue
        seen.add(target)
        selected.append({**by_id[target], 'retrieval': {'reason': 'accepted-current-relationship',
                         'relationship_id': relation['relationship_id'], 'hops': 1,
                         'method': 'accepted-edge-expansion-v1', 'freshness': 'hash-verified-current'}})
    selected_ids = {item['artifact_id'] for item in selected}
    exclusions.extend({'artifact_id': item['artifact_id'], 'reason': 'not_ranked_within_file_budget'}
                      for item in eligible if item['artifact_id'] not in selected_ids)
    diagnostics = {'query': query, 'method': 'fts5-unicode61-bm25-heading4-body1-v1',
                   'index_schema_version': SCHEMA_VERSION, 'max_hops': 1,
                   'candidate_limit': MAX_CANDIDATES, 'candidate_count': len(candidates),
                   'index_signature': signature, 'exclusions': exclusions}
    # Detailed diagnostics are local, disposable metadata. Keep only a labeled
    # sample in the context envelope so excluded candidates cannot consume it.
    payload = (json.dumps(diagnostics, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    digest = hashlib.sha256(payload).hexdigest()
    relative = CACHE_ROOT / 'retrieval' / f'{digest}.json'
    _write_atomic(root / relative, payload)
    return selected, {**diagnostics, 'exclusions': exclusions[:5],
                      'excluded_count': len(exclusions),
                      'exclusion_counts': dict(sorted(Counter(item['reason'] for item in exclusions).items())),
                      'exclusions_omitted': max(0, len(exclusions) - 5),
                      'details_path': relative.as_posix(), 'details_hash': digest}
