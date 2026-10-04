# SPDX-License-Identifier: AGPL-3.0-or-later
"""One deterministic serialized-byte ceiling for governed context envelopes.

max_tokens is a compatibility estimate: four UTF-8 JSON bytes per estimated
 token, not a tokenizer-independent guarantee. Transport wrappers are not exports.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any

from mirrorarc.relationships.model import canonical_json, stable_id


def serialize(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode('utf-8')


def bound_export(document: dict[str, Any]) -> bytes:
    """Drop whole evidence items (never falsify spans); fail if overhead cannot fit."""
    from mirrorarc.context_assembly.builder import ContextAssemblyError

    budget = document['budgets']
    ceiling = int(budget['max_tokens']) * 4
    budget.update(max_export_bytes=ceiling, method='utf8-json-bytes-v1',
                  token_estimate_method='ceil(serialized_bytes/4); no strict token guarantee')
    while True:
        items = document.get('items', [])
        ids = {item['artifact_id'] for item in items}
        if 'relationships' in document:
            document['relationships'] = [r for r in document['relationships']
                                         if r['source_artifact_id'] in ids and r['target_artifact_id'] in ids]
        if 'citations' in document:
            paths = {item.get('path') for item in items}
            document['citations'] = [c for c in document['citations'] if c.get('path') in paths]
        budget['used_excerpt_chars'] = sum(len(item.get('excerpt', '')) for item in items)
        document['offline_complete'] = bool(items) and not document.get('omissions') and all(item.get('excerpt') for item in items)
        # Effective policy changes must not rewrite history under an existing ID.
        # Only timestamps and derived accounting are excluded from identity.
        identity = {k: v for k, v in document.items() if k not in {'context_id', 'created_at', 'budgets', 'freshness'}}
        identity['effective_policy'] = {key: budget[key] for key in
                                        ('max_tokens', 'max_files', 'max_excerpt_chars', 'method')}
        dependency_hash = hashlib.sha256(canonical_json(identity).encode('utf-8')).hexdigest()
        document['freshness']['dependency_hash'] = dependency_hash
        document['context_id'] = stable_id('context', 'frozen-export-v3', dependency_hash)
        for _ in range(8):
            payload = serialize(document)
            size = len(payload)
            if budget.get('serialized_bytes') == size and budget.get('estimated_tokens') == math.ceil(size / 4):
                break
            budget['serialized_bytes'] = size
            budget['estimated_tokens'] = math.ceil(size / 4)
        payload = serialize(document)
        if len(payload) <= ceiling:
            return payload
        if not items:
            raise ContextAssemblyError(f'export overhead exceeds {ceiling} UTF-8 bytes; increase max_tokens estimate within profile policy')
        removed = items.pop()
        document['omissions'].append({'artifact_id': removed['artifact_id'],
                                      'path': removed.get('path', removed.get('source_path', '')),
                                      'reason': 'serialized_export_byte_budget'})


def publish_frozen(root: Path, relative: Path, document: dict[str, Any], *, known: bool) -> tuple[bytes, bool]:
    """Publish once, without replacing history, including after derived-state loss."""
    from mirrorarc.context_assembly.builder import ContextAssemblyError

    if relative.is_absolute() or '..' in relative.parts:
        raise ContextAssemblyError('frozen output must be vault-relative')
    if any(root.joinpath(*relative.parts[:i]).is_symlink() for i in range(1, len(relative.parts) + 1)):
        raise ContextAssemblyError('frozen output may not traverse symlinks')
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)

    def compare_existing() -> tuple[bytes, bool]:
        if path.is_symlink() or not path.is_file():
            raise ContextAssemblyError('frozen output is not a regular file')
        previous = path.read_bytes()
        if not known:
            try:
                saved = json.loads(previous)
                if not isinstance(saved, dict) or not isinstance(saved.get('created_at'), str):
                    raise ValueError('missing creation timestamp')
                document['created_at'] = saved['created_at']
            except (ValueError, UnicodeDecodeError) as exc:
                raise ContextAssemblyError('existing frozen evidence is unreadable; preserve it for review') from exc
        payload = bound_export(document)
        if payload != previous:
            raise ContextAssemblyError('refusing to overwrite different frozen evidence at the same identity; preserve it for review')
        return previous, False

    if path.exists():
        return compare_existing()
    payload = bound_export(document)
    # Hard-link publication is atomic and exclusive: a concurrent writer cannot be
    # overwritten. Both the temporary inode and destination live on one filesystem.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.frozen-', suffix='.tmp', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            return compare_existing()
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return payload, True


def trim_code_evidence(evidence: dict[str, Any], limit: int) -> tuple[str, list[dict[str, int]], bool]:
    """Keep complete exact lines only when applying a per-excerpt character cap."""
    lines = iter(evidence.get('excerpt', '').splitlines(keepends=True))
    included = []
    ranges: list[dict[str, int]] = []
    used = 0
    for span in evidence.get('line_ranges', []):
        for number in range(span['start'], span['end'] + 1):
            line = next(lines, '')
            if used + len(line) > limit:
                return ''.join(included), ranges, True
            included.append(line)
            used += len(line)
            if ranges and ranges[-1]['end'] + 1 == number:
                ranges[-1]['end'] = number
            else:
                ranges.append({'start': number, 'end': number})
    return ''.join(included), ranges, bool(evidence.get('truncated'))


def bound_metadata(manifest: dict[str, Any], budgets: dict[str, int], *, item_key: str = "items", identity_key: str = "artifact_id") -> bytes:
    """Budget the exported selection JSON; never include relationship excerpts."""
    from mirrorarc.context_assembly.builder import ContextAssemblyError
    for relationship in manifest.get('relationships', []):
        for evidence in relationship.get('evidence', []):
            evidence.pop('excerpt', None)
    manifest['budgets'] = {**budgets, 'max_export_bytes': budgets['max_tokens'] * 4,
                           'method': 'utf8-json-bytes-v1',
                           'token_estimate_method': 'ceil(serialized_bytes/4); no strict token guarantee'}
    manifest.setdefault('omissions', [])
    while True:
        ids = {item[identity_key] for item in manifest[item_key]}
        if 'citations' in manifest:
            manifest['citations'] = [c for c in manifest['citations'] if c.get(identity_key) in ids]
        manifest['relationships'] = [r for r in manifest.get('relationships', []) if r['source_artifact_id'] in ids and r['target_artifact_id'] in ids]
        manifest['selection_count'] = len(manifest[item_key])
        for _ in range(8):
            size = len(serialize(manifest))
            if manifest['budgets'].get('serialized_bytes') == size:
                break
            manifest['budgets']['serialized_bytes'] = size
            manifest['budgets']['estimated_tokens'] = math.ceil(size / 4)
        payload = serialize(manifest)
        if len(payload) <= budgets['max_tokens'] * 4 and len(manifest[item_key]) <= budgets['max_files']:
            return payload
        if not manifest[item_key]:
            raise ContextAssemblyError('metadata export overhead exceeds profile byte ceiling')
        removed = manifest[item_key].pop()
        manifest['omissions'].append({identity_key: removed[identity_key], 'reason': 'metadata_export_budget'})
