# SPDX-License-Identifier: AGPL-3.0-or-later
"""PageIndex boundary tests. Mock contracts are distinct from real SDK proof."""
import hashlib
import json
import os
from pathlib import Path

import pytest
import yaml

from mirrorarc.context_assembly.builder import freeze_context, resolve_dynamic_context
from mirrorarc.context_assembly.store import ContextStore
from mirrorarc.document_intelligence import service
from mirrorarc.document_intelligence.adapter import DocumentIntelligenceError, load_model_config
from mirrorarc.document_intelligence.context import build_document_context
from mirrorarc.relationships.deterministic import refresh
from test_context_assembly import copy_template


def fixture_source(tmp_path):
    root = copy_template(tmp_path)
    path = root / '20_sources/example.pdf'
    path.write_bytes(b'%PDF-1.4\nSynthetic fake adapter input, not a parseable PDF.\n')
    manifest = {'records': [{'source_id': 'src_example', 'current_source_path': '20_sources/example.pdf',
                             'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'lifecycle_state': 'clean'}]}
    (root / '_meta/source-manifest.json').write_text(json.dumps(manifest))
    refresh(root)
    return root, path, manifest


def fake_result():
    return {'tree': [{'node_id': 'n1', 'title': 'Synthetic structure', 'start_index': 1, 'end_index': 2}],
            'pages': [{'page_index': 1, 'markdown': 'Synthetic inspection: every 30 days.'},
                      {'page_index': 2, 'markdown': 'Synthetic evidence, not operating advice.'}],
            'provider_doc_id': 'pi-synthetic', 'provider_version': service.SUPPORTED_VERSION,
            'parser': 'pypdf', 'parser_version': service.PARSER_VERSION, 'pdfium_version': service.PDFIUM_VERSION,
            'method': 'pageindex-flash-model-free', 'usage': {'requests': 0}}


def test_index_context_source_change_and_recovery(tmp_path, monkeypatch):
    root, source, manifest = fixture_source(tmp_path)
    calls = []
    def fake(request, **kwargs):
        assert Path(request['source']) != source
        assert Path(request['source']).read_bytes() == source.read_bytes()
        calls.append(request)
        return fake_result()
    monkeypatch.setattr(service, 'run_worker', fake)
    original = source.read_bytes()
    first = service.index_document(root, 'src_example')
    assert service.index_document(root, 'src_example')['unchanged']
    assert len(calls) == 1
    built = build_document_context(root, 'src_example', [1, 2])
    definition_id = built['definition']['definition_id']
    assert 'Synthetic inspection' not in json.dumps(resolve_dynamic_context(root, definition_id))
    pack = freeze_context(root, definition_id=definition_id)
    output = root / pack['output_path']
    before = output.read_bytes()
    assert pack['document']['items'][0]['page'] == 1
    assert 'every 30 days' in pack['document']['items'][0]['excerpt']
    with ContextStore(root).connect() as connection:
        connection.execute('DELETE FROM context_packs')
    refresh(root)
    assert freeze_context(root, definition_id=definition_id)['unchanged']
    source.write_bytes(original + b'changed\n')
    with pytest.raises(DocumentIntelligenceError, match='changed'):
        service.load_index(root, 'src_example')
    assert ContextStore(root).status(pack['context_id'])['packs'][0]['freshness_state'] == 'stale'
    assert output.read_bytes() == before
    manifest['records'][0]['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    (root / '_meta/source-manifest.json').write_text(json.dumps(manifest))
    refresh(root)
    second = service.index_document(root, 'src_example')
    assert first['index_id'] != second['index_id']
    assert output.read_bytes() == before


def test_validation_and_failed_refresh_preserve_previous(tmp_path, monkeypatch):
    root, source, _ = fixture_source(tmp_path)
    monkeypatch.setattr(service, 'run_worker', lambda *a, **k: fake_result())
    first = service.index_document(root, 'src_example')
    invalid = fake_result()
    invalid['tree'][0]['end_index'] = 3
    monkeypatch.setattr(service, 'run_worker', lambda *a, **k: invalid)
    with pytest.raises(DocumentIntelligenceError, match='bounds'):
        service.index_document(root, 'src_example', force=True)
    assert service.load_index(root, 'src_example')['index_id'] == first['index_id']
    result = service.load_index(root, 'src_example')
    assert service.validate_citations('<cite doc="pi-synthetic" page="2"/>', result)[0]['claim_support'] == 'not-reviewed'
    for text in ['No citation.', '<cite doc="other" page="1"/>', '<cite doc="pi-synthetic" page="999"/>']:
        with pytest.raises(DocumentIntelligenceError):
            service.validate_citations(text, result)
    path = root / service.CACHE_ROOT / 'src_example' / (first['index_id'] + '.json')
    value = json.loads(path.read_text())
    value['pages'][0]['markdown'] = 'modified cache'
    path.write_text(json.dumps(value))
    with pytest.raises(DocumentIntelligenceError, match='hash mismatch'):
        service.load_index(root, 'src_example')


def test_model_opt_in_policy_and_confinement(tmp_path, monkeypatch):
    root, _, _ = fixture_source(tmp_path)
    monkeypatch.setattr(service, 'run_worker', lambda *a, **k: pytest.fail('provider must not be called'))
    with pytest.raises(DocumentIntelligenceError, match='opt-in'):
        service.index_document(root, 'src_example', model_assisted=True)
    with pytest.raises(DocumentIntelligenceError):
        service.index_document(root, '../outside')
    with pytest.raises(DocumentIntelligenceError, match='standard'):
        service.index_document(root, 'src_example', index_mode='standard')
    config = {'model': 'synthetic', 'base_url': 'https://example.invalid/v1', 'api_key_env': 'SYNTHETIC_KEY',
              'max_requests': 2, 'max_output_tokens': 128, 'max_request_bytes': 4096}
    monkeypatch.setenv('SYNTHETIC_KEY', 'synthetic-test-credential')
    (root / '_meta/pageindex.yml').write_text(yaml.safe_dump(config))
    assert load_model_config(root, True) == config
    for endpoint in ['http://remote.invalid/v1', 'https://name:secret@example.invalid/v1', 'https://example.invalid/v1?key=secret']:
        (root / '_meta/pageindex.yml').write_text(yaml.safe_dump({**config, 'base_url': endpoint}))
        with pytest.raises(DocumentIntelligenceError):
            load_model_config(root, True)
    cache = root / '.mirrorarc/cache'
    cache.mkdir(exist_ok=True)
    (cache / 'pageindex').symlink_to(tmp_path / 'elsewhere', target_is_directory=True)
    with pytest.raises(DocumentIntelligenceError, match='symlinks'):
        service.index_document(root, 'src_example')


def test_catalog_only_embeds_pdf_text_when_explicit(tmp_path, monkeypatch):
    root, _, _ = fixture_source(tmp_path)
    monkeypatch.setattr(service, 'run_worker', lambda *a, **k: fake_result())
    service.index_document(root, 'src_example')
    metadata = service.catalog_report(root)
    assert 'Synthetic inspection' not in json.dumps(metadata)
    content = service.catalog_report(root, include_content=True)
    assert 'Synthetic inspection' in json.dumps(content)
    assert content['items'][0]['pages'][0]['text_hash']


def test_document_status_does_not_initialize_an_unused_database(tmp_path):
    root = copy_template(tmp_path)
    assert service.status_report(root)['items'] == []
    assert not (root / '.mirrorarc/state.sqlite').exists()


@pytest.mark.skipif(not os.environ.get('MIRRORARC_PAGEINDEX_PYTHON'), reason='explicit isolated real PageIndex runtime required')
def test_real_pageindex_model_free_pdf(tmp_path):
    pytest.importorskip('reportlab')
    from scripts.pageindex_product_proof import synthetic_pdf
    root, source, manifest = fixture_source(tmp_path)
    synthetic_pdf(source)
    manifest['records'][0]['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    (root / '_meta/source-manifest.json').write_text(json.dumps(manifest))
    refresh(root)
    result = service.index_document(root, 'src_example')
    assert result['page_count'] == 3
    assert result['usage']['requests'] == 0
    assert 'every 30 days' in service.load_index(root, 'src_example')['pages'][1]['markdown']


@pytest.mark.skipif(not os.environ.get('MIRRORARC_PAGEINDEX_PYTHON'), reason='explicit isolated real PageIndex runtime required')
def test_real_assisted_index_transport_with_scripted_loopback(tmp_path, monkeypatch):
    pytest.importorskip('reportlab')
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from scripts.pageindex_product_proof import synthetic_pdf
    root, source, manifest = fixture_source(tmp_path)
    synthetic_pdf(source)
    manifest['records'][0]['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    (root / '_meta/source-manifest.json').write_text(json.dumps(manifest))
    refresh(root)
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            payload = json.dumps({'id': 'chatcmpl_scripted', 'object': 'chat.completion', 'created': 0,
                                  'model': 'synthetic', 'choices': [{'index': 0, 'finish_reason': 'stop',
                                  'message': {'role': 'assistant', 'content': '{"summary":"Scripted synthetic summary."}'}}],
                                  'usage': {'prompt_tokens': 10, 'completion_tokens': 10, 'total_tokens': 20}}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        config = {'model': 'synthetic', 'base_url': f'http://127.0.0.1:{server.server_port}/v1',
                  'api_key_env': 'SYNTHETIC_KEY', 'max_requests': 4, 'max_output_tokens': 512, 'max_request_bytes': 100000}
        monkeypatch.setenv('SYNTHETIC_KEY', 'synthetic-test-credential')
        (root / '_meta/pageindex.yml').write_text(yaml.safe_dump(config))
        result = service.index_document(root, 'src_example', model_assisted=True, allow_model=True)
        assert result['method'] == 'pageindex-flash-model-assisted'
        assert 1 <= result['usage']['requests'] == len(requests) <= 4
        assert all(request['model'] == 'synthetic' and request['store'] is False for request in requests)
        assert result['source_hash'] == hashlib.sha256(source.read_bytes()).hexdigest()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.mark.skipif(not os.environ.get('MIRRORARC_PAGEINDEX_PYTHON'), reason='explicit isolated real PageIndex runtime required')
def test_real_sdk_reasoning_tools_against_scripted_loopback_not_model_quality(tmp_path, monkeypatch):
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from mirrorarc.document_intelligence.adapter import run_worker

    root, _, _ = fixture_source(tmp_path)
    # This test uses a scripted HTTP peer, NOT a real model or quality evaluation.
    monkeypatch.setattr(service, 'run_worker', lambda *a, **k: fake_result())
    service.index_document(root, 'src_example')
    monkeypatch.setattr(service, 'run_worker', run_worker)
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(body)
            if len(requests) == 1:
                output = [{'id': 'fc_synthetic', 'type': 'function_call', 'call_id': 'call_synthetic',
                           'name': 'get_page_content', 'arguments': json.dumps({'doc_name': 'source.pdf', 'pages': '1', 'folder_id': None})}]
            else:
                output = [{'id': 'msg_synthetic', 'type': 'message', 'role': 'assistant', 'status': 'completed',
                           'content': [{'type': 'output_text', 'annotations': [],
                                        'text': 'The fictional interval is 30 days. <cite doc="pi-synthetic" page="1"/>'}]}]
            value = {'id': 'resp_synthetic', 'object': 'response', 'created_at': 0, 'status': 'completed',
                     'model': 'synthetic', 'output': output,
                     'usage': {'input_tokens': 10, 'output_tokens': 10, 'total_tokens': 20}}
            payload = json.dumps(value).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        config = {'model': 'synthetic', 'base_url': f'http://127.0.0.1:{server.server_port}/v1',
                  'api_key_env': 'SYNTHETIC_KEY', 'max_requests': 4, 'max_output_tokens': 512, 'max_request_bytes': 100000}
        monkeypatch.setenv('SYNTHETIC_KEY', 'synthetic-test-credential')
        (root / '_meta/pageindex.yml').write_text(yaml.safe_dump(config))
        result = service.ask_document(root, 'src_example', 'What is the fictional inspection interval?', allow_model=True)
        assert result['review_state'] == 'unreviewed'
        assert result['usage']['requests'] == 2
        assert 'Synthetic inspection' in json.dumps(requests[1]['input'])
        assert all(request.get('store') is False for request in requests)
        assert all(tool['name'] != 'remove_document' for tool in requests[0]['tools'])
        assert result['citations'][0]['page'] == 1
        assert (root / result['context_path']).is_file()
        assert (root / result['output_path']).is_file()
        preview = service.catalog_report(root, include_content=True)['items'][0]['answers'][0]
        assert preview['answer'].endswith('[physical page 1]')
        assert preview['evidence'][0]['excerpt'] == fake_result()['pages'][0]['markdown']
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
