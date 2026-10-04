# SPDX-License-Identifier: AGPL-3.0-or-later
"""Source-bound PageIndex results. Local JSON caches are never source authority."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import xml.etree.ElementTree as ET

from mirrorarc.context_assembly.builder import _safe_path, require_mode
from mirrorarc.document_intelligence.adapter import DocumentIntelligenceError, load_model_config, read_bounded, run_worker, SUPPORTED_VERSION, PARSER_VERSION, PDFIUM_VERSION
from mirrorarc.relationships.model import EvidenceAnchor, canonical_json, stable_id
from mirrorarc.relationships.store import RelationshipStore

from mirrorarc.document_intelligence.presentation import CONTRACT, INSTRUCTIONS, read_presentation

CACHE_ROOT = Path('.mirrorarc/cache/pageindex')
MAX_PDF_BYTES = 32 * 1024 * 1024
MAX_CACHE_BYTES = 12_000_000


def _digest(value) -> str:
    return hashlib.sha256(canonical_json(value).encode('utf-8')).hexdigest()


def _cache_path(root: Path, relative: Path) -> Path:
    if relative.is_absolute() or '..' in relative.parts or not relative.is_relative_to(CACHE_ROOT):
        raise DocumentIntelligenceError('invalid document cache path')
    if any(root.joinpath(*relative.parts[:i]).is_symlink() for i in range(1, len(relative.parts) + 1)):
        raise DocumentIntelligenceError('document cache may not traverse symlinks')
    return root / relative


def _write(root: Path, relative: Path, value: dict, *, immutable=False):
    path = _cache_path(root, relative)
    payload = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    if len(payload) > MAX_CACHE_BYTES:
        raise DocumentIntelligenceError('document evidence exceeds its cache byte limit')
    if path.is_file():
        if read_bounded(path, MAX_CACHE_BYTES, 'Document cache') == payload:
            return
        if immutable:
            raise DocumentIntelligenceError('refusing to overwrite historical document evidence')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.pageindex-', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if immutable:
            try:
                os.link(temporary, path)
            except FileExistsError:
                if read_bounded(path, MAX_CACHE_BYTES, 'Document cache') != payload:
                    raise DocumentIntelligenceError('concurrent document evidence conflict')
        else:
            os.replace(temporary, path)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def source_record(root: Path, source_id: str) -> tuple[dict, Path]:
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}', source_id):
        raise DocumentIntelligenceError('use the source ID printed by mirrorarc status --json')
    artifacts = RelationshipStore(root).export(current_only=True)['artifacts']
    source = next((item for item in artifacts if item['artifact_id'] == source_id and item['artifact_kind'] == 'source'), None)
    if not source or source['lifecycle_state'] not in {'current', 'clean', 'active'}:
        raise DocumentIntelligenceError('a current registered PDF is required; run mirrorarc sync first')
    path = _safe_path(root, source['path'])
    if not path or path.suffix.lower() != '.pdf':
        raise DocumentIntelligenceError('source must be a vault-confined regular PDF no larger than 32 MiB')
    if hashlib.sha256(read_bounded(path, MAX_PDF_BYTES, 'Source PDF')).hexdigest() != source['content_hash']:
        raise DocumentIntelligenceError('source has changed; sync and reindex before using current evidence')
    return source, path


def validate_tree(tree, page_count: int) -> list[dict]:
    """Reject impossible citations, oversized trees and malformed model output."""
    count = 0
    seen = set()

    def walk(nodes, depth=0, parent=None):
        nonlocal count
        if not isinstance(nodes, list) or depth > 16:
            raise DocumentIntelligenceError('invalid or excessively deep PageIndex tree')
        result = []
        for node in nodes:
            count += 1
            if not isinstance(node, dict) or count > 2000:
                raise DocumentIntelligenceError('invalid or oversized PageIndex tree')
            start, end, identity = node.get('start_index'), node.get('end_index'), node.get('node_id')
            if (type(start) is not int or type(end) is not int or not 1 <= start <= end <= page_count
                    or (parent and not parent[0] <= start <= end <= parent[1])
                    or not isinstance(identity, str) or not identity or len(identity) > 100 or identity in seen):
                raise DocumentIntelligenceError('PageIndex node IDs or physical page bounds are invalid')
            title, summary = node.get('title', ''), node.get('summary', '')
            if not isinstance(title, str) or not isinstance(summary, str) or len(title) > 1000 or len(summary) > 12000:
                raise DocumentIntelligenceError('PageIndex node text exceeds contract limits')
            seen.add(identity)
            result.append({'node_id': identity, 'title': title, 'start_index': start, 'end_index': end,
                           **({'summary': summary} if summary else {}),
                           'nodes': walk(node.get('nodes') or [], depth + 1, (start, end))})
        return result

    normalized = walk(tree)
    if not normalized:
        raise DocumentIntelligenceError('PageIndex returned no document structure')
    return normalized


def _register(root, source, result, relative):
    identity = result['index_id']
    RelationshipStore(root).replace_deterministic_for_artifacts({identity}, [{
        'artifact_id': identity, 'artifact_kind': 'document-evidence', 'layer': 'derived',
        'path': relative.as_posix(), 'title': 'PageIndex document structure', 'domain': source['domain'],
        'content_hash': result['index_hash'], 'lifecycle_state': 'current', 'authority': 'derived',
        'metadata': {'source_id': source['artifact_id'], 'provider': 'PageIndex', 'provider_version': SUPPORTED_VERSION},
    }], [{
        'source_artifact_id': identity, 'target_artifact_id': source['artifact_id'],
        'relationship_type': 'DERIVED_FROM', 'method': 'deterministic', 'method_version': 'pageindex-binding:v1',
        'state': 'accepted', 'source_hash': result['index_hash'], 'target_hash': source['content_hash'],
        'evidence': [EvidenceAnchor(identity, 'source-sha256', source['content_hash'], result['index_hash'])],
    }])


def load_index(root: Path, source_id: str) -> dict:
    source, _ = source_record(root, source_id)
    pointer = _cache_path(root, CACHE_ROOT / source_id / 'current.json')
    try:
        current = json.loads(read_bounded(pointer, 4096, 'Document pointer'))
        relative = CACHE_ROOT / source_id / (current['index_id'] + '.json')
        result = json.loads(read_bounded(_cache_path(root, relative), MAX_CACHE_BYTES, 'Document index'))
        if not isinstance(result, dict):
            raise DocumentIntelligenceError('document index is malformed; preserve evidence and reindex')
        identity = {k: v for k, v in result.items() if k not in {'index_id', 'index_hash'}}
        if (_digest(identity) != result['index_hash'] or result['index_hash'] != current['index_hash']
                or result['index_id'] != current['index_id']
                or result['index_id'] != stable_id('document_index', source_id, result['index_hash'])):
            raise DocumentIntelligenceError('document index hash mismatch; preserve evidence and reindex')
        if (result['source_hash'] != source['content_hash'] or result['source_id'] != source_id
                or result['source_path'] != source['path']):
            raise DocumentIntelligenceError('document index is stale; reindex before asking a question')
        if (result.get('provider_version') != SUPPORTED_VERSION or result.get('parser') != 'pypdf'
                or result.get('parser_version') != PARSER_VERSION or result.get('pdfium_version') != PDFIUM_VERSION):
            raise DocumentIntelligenceError('document parser runtime changed; reindex before using current evidence; historical packs are preserved')
        return result
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as exc:
        if isinstance(exc, DocumentIntelligenceError):
            raise
        raise DocumentIntelligenceError('document index is missing or unreadable; run document index first') from exc


def index_document(root: Path, source_id: str, *, allow_model=False, model_assisted=False, index_mode='flash', python=None, force=False) -> dict:
    root = root.expanduser().resolve()
    require_mode(root, 'metadata')
    if model_assisted:
        require_mode(root, 'frozen')
    config = load_model_config(root, allow_model) if model_assisted else None
    if index_mode not in {'flash', 'standard'} or (index_mode == 'standard' and not model_assisted):
        raise DocumentIntelligenceError('standard indexing requires explicit model-assisted mode')
    source, original = source_record(root, source_id)
    settings = {'model': config['model'], 'base_url': config['base_url'],
                'max_requests': config['max_requests'], 'max_output_tokens': config['max_output_tokens'],
                'max_request_bytes': config['max_request_bytes']} if config else None
    if not force:
        try:
            existing = load_index(root, source_id)
            if existing.get('model_config') == settings and existing['index_mode'] == index_mode:
                return {**index_metadata(existing), 'unchanged': True}
        except DocumentIntelligenceError:
            pass
    directory = _cache_path(root, CACHE_ROOT / source_id)
    directory.mkdir(parents=True, exist_ok=True)
    # Provider sees a private snapshot, never the authoritative PDF itself.
    with tempfile.TemporaryDirectory(prefix='.run-', dir=directory) as scratch:
        snapshot = Path(scratch) / 'source.pdf'
        raw = read_bounded(original, MAX_PDF_BYTES, 'Source PDF')
        if hashlib.sha256(raw).hexdigest() != source['content_hash']:
            raise DocumentIntelligenceError('source changed before snapshot copy')
        snapshot.write_bytes(raw)
        response = run_worker({'action': 'index', 'source': str(snapshot), 'storage': str(Path(scratch) / 'provider'),
                               'model_config': config, 'index_mode': index_mode}, python=python)
        if hashlib.sha256(read_bounded(snapshot, MAX_PDF_BYTES, 'Provider snapshot')).hexdigest() != source['content_hash']:
            raise DocumentIntelligenceError('provider snapshot changed; result not published')
    source_record(root, source_id)  # Refuse publication if original changed during processing.
    if (response.get('provider_version') != SUPPORTED_VERSION or response.get('parser') != 'pypdf'
            or response.get('parser_version') != PARSER_VERSION or response.get('pdfium_version') != PDFIUM_VERSION):
        raise DocumentIntelligenceError('provider parser provenance differs from the supported runtime; result not published')
    pages = response.get('pages')
    if not isinstance(pages, list) or not 1 <= len(pages) <= 500:
        raise DocumentIntelligenceError('invalid PDF page extraction')
    for number, page in enumerate(pages, 1):
        if not isinstance(page, dict) or page.get('page_index') != number or not isinstance(page.get('markdown'), str):
            raise DocumentIntelligenceError('invalid PDF page extraction')
        page['text_hash'] = hashlib.sha256(page['markdown'].encode()).hexdigest()
    if sum(len(page['markdown'].encode()) for page in pages) > 2_000_000 or not any(page['markdown'].strip() for page in pages):
        raise DocumentIntelligenceError('PDF extraction is empty or exceeds its text byte limit')
    tree = validate_tree(response['tree'], len(pages))
    result = {'schema_version': 1, 'source_id': source_id, 'source_path': source['path'],
              'source_hash': source['content_hash'], 'provider': 'PageIndex', 'provider_version': SUPPORTED_VERSION,
              'parser': 'pypdf', 'parser_version': PARSER_VERSION, 'pdfium_version': PDFIUM_VERSION,
              'method': response['method'], 'index_mode': index_mode,
              'model_config': settings, 'provider_doc_id': response['provider_doc_id'],
              'tree': tree, 'pages': pages, 'usage': response['usage'],
              'warnings': ['Physical PDF pages, not printed page labels. Extracted text can omit layout or images.',
                           'Structure and summaries are derived navigation, not accepted claims.'],
              'sensitivity': 'local-sensitive'}
    result['index_hash'] = _digest(result)
    result['index_id'] = stable_id('document_index', source_id, result['index_hash'])
    relative = CACHE_ROOT / source_id / (result['index_id'] + '.json')
    _write(root, relative, result, immutable=True)
    _register(root, source, result, relative)
    _write(root, CACHE_ROOT / source_id / 'current.json', {'index_id': result['index_id'], 'index_hash': result['index_hash']})
    return {**index_metadata(result), 'unchanged': False}


def index_metadata(result: dict) -> dict:
    return {key: result[key] for key in ('index_id', 'index_hash', 'source_id', 'source_path', 'source_hash',
                                        'provider', 'provider_version', 'method', 'warnings', 'usage')} | {
        'page_count': len(result['pages']), 'freshness_state': 'current', 'body_content_included': False}


def validate_citations(answer: str, document: dict) -> list[dict]:
    if not isinstance(answer, str) or len(answer) > 40000:
        raise DocumentIntelligenceError('answer exceeds the safety limit')
    tags = re.findall(r'<cite\b[^>]*?/\s*>', answer)
    if not tags or answer.count('<cite') != len(tags):
        raise DocumentIntelligenceError('answer has missing or malformed citations; no candidate published')
    citations = []
    for tag in tags:
        try:
            node = ET.fromstring(tag)
            page = int(node.attrib['page'])
            if node.attrib.get('doc') != document['provider_doc_id'] or set(node.attrib) != {'doc', 'page'} or not 1 <= page <= len(document['pages']):
                raise ValueError('out of scope')
        except (ValueError, KeyError, ET.ParseError) as exc:
            raise DocumentIntelligenceError('answer cites an unknown document or physical page; no candidate published') from exc
        citation = {'source_id': document['source_id'], 'source_path': document['source_path'],
                    'source_hash': document['source_hash'], 'page': page,
                    'text_hash': document['pages'][page - 1]['text_hash'], 'claim_support': 'not-reviewed'}
        if citation not in citations:
            citations.append(citation)
    return citations


def ask_document(root: Path, source_id: str, question: str, *, allow_model=False, python=None) -> dict:
    root = root.expanduser().resolve()
    require_mode(root, 'frozen')
    config = load_model_config(root, allow_model)
    if not isinstance(question, str) or not question.strip() or len(question) > 4000:
        raise DocumentIntelligenceError('question must contain 1 to 4000 characters')
    document = load_index(root, source_id)
    directory = _cache_path(root, CACHE_ROOT / source_id)
    with tempfile.TemporaryDirectory(prefix='.ask-', dir=directory) as scratch:
        response = run_worker({'action': 'ask', 'document': document, 'question': question,
                               'storage': str(Path(scratch) / 'provider'), 'model_config': config,
                               'answer_instructions': INSTRUCTIONS}, python=python)
    current = load_index(root, source_id)
    if current['index_id'] != document['index_id']:
        raise DocumentIntelligenceError('document changed during the question; no answer published')
    citations = validate_citations(response['answer'], document)
    from mirrorarc.document_intelligence.context import build_document_context
    pack = build_document_context(root, source_id, [citation['page'] for citation in citations], task=question, mode='frozen')
    if pack['document']['omissions'] or {item['page'] for item in pack['document']['items']} != {citation['page'] for citation in citations}:
        raise DocumentIntelligenceError('cited pages do not fit current context policy; narrow the question before publishing an answer')
    if any(item['index_id'] != document['index_id'] or item['source_hash'] != document['source_hash']
           or item['page_text_hash'] != document['pages'][item['page'] - 1]['text_hash']
           for item in pack['document']['items']):
        raise DocumentIntelligenceError('document changed while freezing cited pages; no answer published')
    if load_index(root, source_id)['index_id'] != document['index_id']:
        raise DocumentIntelligenceError('document changed before answer publication; no answer published')
    result = {'question': question, 'answer': response['answer'], 'citations': citations,
            'presentation_contract': CONTRACT,
            'index_id': document['index_id'], 'source_id': source_id, 'source_hash': document['source_hash'],
            'context_id': pack['context_id'], 'context_path': pack['output_path'], 'context_hash': pack['output_hash'],
            'model': config['model'], 'endpoint': config['base_url'], 'usage': response['usage'],
            'review_state': 'unreviewed', 'freshness_state': 'current', 'sensitivity': 'local-sensitive',
            'warnings': ['Citation addresses were checked; whether each claim is supported still requires review.',
                         'This is model-generated interpretation, not an authoritative record.']}
    result['answer_id'] = stable_id('answer', _digest(result))
    relative = CACHE_ROOT / source_id / 'answers' / (result['answer_id'] + '.json')
    _write(root, relative, result, immutable=True)
    return {**result, 'output_path': relative.as_posix()}


def status_report(root: Path, source_id: str | None = None) -> dict:
    root = root.expanduser().resolve()
    store = RelationshipStore(root)
    if not store.path.is_file():
        return {'provider': 'PageIndex', 'items': []}
    sources = [item for item in store.export(current_only=True)['artifacts']
               if item['artifact_kind'] == 'source' and item['path'].lower().endswith('.pdf')
               and (source_id is None or source_id == item['artifact_id'])]
    items = []
    for source in sources:
        try:
            items.append(index_metadata(load_index(root, source['artifact_id'])))
        except DocumentIntelligenceError as exc:
            items.append({'source_id': source['artifact_id'], 'source_path': source['path'],
                          'freshness_state': 'attention', 'reason': str(exc), 'body_content_included': False})
    return {'provider': 'PageIndex', 'items': items}


def _answer_previews(root: Path, item: dict, include_content: bool, allowance: int) -> tuple[list[dict], int]:
    """Inspect bounded immutable candidates, never accept them or regenerate answers."""
    directory = _cache_path(root, CACHE_ROOT / item['source_id'] / 'answers')
    if not directory.is_dir():
        return [], allowance
    # Avoid enumerating an unbounded history in every portable Catalog. This is
    # a bounded selection, not a promise to display the newest five answers.
    paths = []
    with os.scandir(directory) as entries:
        for entry in entries:
            if len(paths) == 5:
                item['answer_history_bounded'] = True
                break
            if re.fullmatch(r'answer_[a-f0-9]+\.json', entry.name):
                paths.append(Path(entry.path))
    previews = []
    for path in sorted(paths):
        try:
            candidate = json.loads(read_bounded(path, MAX_CACHE_BYTES, 'Answer candidate'))
            identity = {key: value for key, value in candidate.items() if key != 'answer_id'}
            if (candidate['answer_id'] != path.stem or stable_id('answer', _digest(identity)) != path.stem
                    or candidate['source_id'] != item['source_id']):
                raise DocumentIntelligenceError('answer identity mismatch')
            context_id = candidate['context_id']
            expected_path = f'.mirrorarc/cache/context/{context_id}.frozen.json'
            if not re.fullmatch(r'context_[a-f0-9]+', context_id) or candidate['context_path'] != expected_path:
                raise DocumentIntelligenceError('answer context path is invalid')
            context_path = _safe_path(root, expected_path)
            if context_path is None:
                raise DocumentIntelligenceError('answer context is missing')
            raw = read_bounded(context_path, MAX_CACHE_BYTES, 'Answer frozen evidence')
            if hashlib.sha256(raw).hexdigest() != candidate['context_hash']:
                raise DocumentIntelligenceError('answer context hash mismatch')
            pack = json.loads(raw)
            if pack['context_id'] != context_id or pack['omissions']:
                raise DocumentIntelligenceError('answer context is incomplete')
            excerpts = []
            for citation in candidate['citations']:
                evidence = next((value for value in pack['items'] if value['page'] == citation['page']
                                 and value['artifact_id'] == candidate['source_id']), None)
                if (not evidence or evidence['source_hash'] != candidate['source_hash']
                        or evidence['page_text_hash'] != citation['text_hash']
                        or hashlib.sha256(evidence['excerpt'].encode()).hexdigest() != evidence['excerpt_hash']):
                    raise DocumentIntelligenceError('answer citation does not match frozen evidence')
                excerpts.append({'page': citation['page'], 'excerpt': evidence['excerpt'],
                                 'source_path': citation['source_path'], 'text_hash': citation['text_hash']})
            current = (item.get('freshness_state') == 'current'
                       and item.get('index_id') == candidate['index_id']
                       and item.get('source_hash') == candidate['source_hash']
                       and all(citation['source_path'] == item['source_path'] for citation in candidate['citations']))
            preview = {'answer_id': candidate['answer_id'], 'context_id': context_id,
                       'context_path': expected_path, 'context_hash': candidate['context_hash'],
                       'source_hash': candidate['source_hash'], 'model': candidate['model'],
                       'freshness_state': 'current' if current else 'stale', 'review_state': 'unreviewed',
                       'body_content_included': False}
            if include_content:
                content = {'question': candidate['question'], 'original_answer': candidate['answer'],
                           'answer': re.sub(r'<cite\b[^>]*?page=["\'](\d+)["\'][^>]*?/\s*>',
                                            lambda match: f'[physical page {int(match[1])}]', candidate['answer']),
                           'presentation': read_presentation(candidate['answer'],
                                                            candidate.get('presentation_contract'), candidate['citations']),
                           'evidence': excerpts}
                # Count duplicated presentation text too; never omit a field or citation to fit.
                size = len(json.dumps(content, ensure_ascii=False))
                if size <= allowance:
                    allowance -= size
                    preview.update(content, body_content_included=True)
                else:
                    preview['omission'] = 'answer preview exceeds the remaining Catalog content budget'
            previews.append(preview)
        except (DocumentIntelligenceError, ValueError, KeyError, TypeError, AttributeError, RecursionError):
            previews.append({'answer_id': path.stem, 'freshness_state': 'unavailable',
                             'review_state': 'unreviewed', 'body_content_included': False,
                             'reason': 'Candidate or frozen evidence is missing, changed or malformed; no answer text shown.'})
    return previews, allowance


def catalog_report(root: Path, *, include_content=False) -> dict:
    import shlex
    result = status_report(root)
    remaining = 100000
    for item in result['items']:
        item['next_command'] = 'mirrorarc --root ' + shlex.quote(str(root)) + ' document index --source ' + shlex.quote(item['source_id'])
        try:
            item['answers'], remaining = _answer_previews(root, item, include_content, remaining)
        except (OSError, DocumentIntelligenceError):
            item['answer_history_unavailable'] = True
        if not include_content or item['freshness_state'] != 'current':
            continue
        try:
            document = load_index(root, item['source_id'])
        except DocumentIntelligenceError as exc:
            item.update(freshness_state='attention', reason=str(exc))
            continue
        nodes = []
        def walk(tree, depth=0):
            for node in tree:
                if len(nodes) >= 100:
                    return
                nodes.append({'title': node['title'], 'start_page': node['start_index'],
                              'end_page': node['end_index'], 'depth': depth})
                walk(node['nodes'], depth + 1)
        walk(document['tree'])
        item['nodes'] = nodes
        item['pages'] = []
        allowance = min(remaining, 20000)
        for page in document['pages']:
            if allowance <= 0:
                break
            excerpt = page['markdown'][:min(3000, allowance)]
            allowance -= len(excerpt)
            remaining -= len(excerpt)
            item['pages'].append({'page': page['page_index'], 'excerpt': excerpt, 'text_hash': page['text_hash'],
                                  'truncated': len(excerpt) != len(page['markdown'])})
        item['body_content_included'] = True
        item['omitted_pages'] = len(document['pages']) - len(item['pages'])
    result['content_included'] = include_content
    return result


def reconcile_indexes(root: Path) -> list[str]:
    """Reattach disposable current index metadata after the existing full refresh."""
    if not (root / CACHE_ROOT).is_dir():
        return []
    restored = []
    for item in status_report(root)['items']:
        if item['freshness_state'] != 'current':
            continue
        source, _ = source_record(root, item['source_id'])
        result = load_index(root, item['source_id'])
        _register(root, source, result, CACHE_ROOT / item['source_id'] / (result['index_id'] + '.json'))
        restored.append(result['index_id'])
    return restored
