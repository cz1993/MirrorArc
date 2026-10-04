# SPDX-License-Identifier: AGPL-3.0-or-later
"""Privacy and resource-limit regressions; no external inference is used."""
import json
import os
from pathlib import Path
import subprocess
import venv

import pytest
import yaml

from mirrorarc.document_intelligence import adapter
from test_context_assembly import copy_template
from test_document_intelligence import fake_result, fixture_source


def test_bounded_reads_refuse_large_files_symlinks_and_pipes(tmp_path):
    path = tmp_path / 'regular'
    path.write_bytes(b'synthetic')
    assert adapter.read_bounded(path, 9, 'Fixture') == b'synthetic'
    with pytest.raises(adapter.DocumentIntelligenceError, match='byte limit'):
        adapter.read_bounded(path, 8, 'Fixture')
    link = tmp_path / 'link'
    link.symlink_to(path)
    with pytest.raises(adapter.DocumentIntelligenceError, match='regular file'):
        adapter.read_bounded(link, 9, 'Fixture')
    fifo = tmp_path / 'pipe'
    os.mkfifo(fifo)
    with pytest.raises(adapter.DocumentIntelligenceError, match='regular file'):
        adapter.read_bounded(fifo, 9, 'Fixture')


def test_moved_source_requires_new_path_binding(tmp_path, monkeypatch):
    from mirrorarc.document_intelligence import service
    from mirrorarc.relationships.deterministic import refresh
    root, path, manifest = fixture_source(tmp_path)
    monkeypatch.setattr(service, 'run_worker', lambda *args, **kwargs: fake_result())
    before = service.index_document(root, 'src_example')
    path.rename(path.with_name('renamed.pdf'))
    manifest['records'][0]['current_source_path'] = '20_sources/renamed.pdf'
    (root / '_meta/source-manifest.json').write_text(json.dumps(manifest))
    refresh(root)
    with pytest.raises(adapter.DocumentIntelligenceError, match='stale'):
        service.load_index(root, 'src_example')
    after = service.index_document(root, 'src_example')
    assert after['source_path'] == '20_sources/renamed.pdf'
    assert after['index_id'] != before['index_id']


def test_answer_cannot_bind_a_newer_pack_to_old_citations(tmp_path, monkeypatch):
    from mirrorarc.document_intelligence import context, service
    root, _, _ = fixture_source(tmp_path)
    monkeypatch.setattr(service, 'run_worker', lambda *args, **kwargs: fake_result())
    service.index_document(root, 'src_example')
    config = {'model': 'synthetic', 'base_url': 'http://127.0.0.1:1/v1', 'api_key_env': 'SYNTHETIC_KEY',
              'max_requests': 2, 'max_output_tokens': 128, 'max_request_bytes': 4096}
    (root / '_meta/pageindex.yml').write_text(yaml.safe_dump(config))
    monkeypatch.setenv('SYNTHETIC_KEY', 'synthetic-test-credential')
    monkeypatch.setattr(service, 'run_worker', lambda *args, **kwargs: {
        'answer': '30 days. <cite doc="pi-synthetic" page="1"/>', 'usage': {'requests': 0}})
    original = context.build_document_context
    def changed_pack(*args, **kwargs):
        result = original(*args, **kwargs)
        result['document']['items'][0]['index_id'] = 'different-index'
        return result
    monkeypatch.setattr(context, 'build_document_context', changed_pack)
    with pytest.raises(adapter.DocumentIntelligenceError, match='changed while freezing'):
        service.ask_document(root, 'src_example', 'What is the interval?', allow_model=True)
    assert not (root / service.CACHE_ROOT / 'src_example/answers').exists()


def test_answer_review_uses_frozen_evidence_and_fails_closed_on_tamper(tmp_path, monkeypatch):
    from mirrorarc.document_intelligence import service
    root, source, _ = fixture_source(tmp_path)
    monkeypatch.setattr(service, 'run_worker', lambda *args, **kwargs: fake_result())
    service.index_document(root, 'src_example')
    config = {'model': 'synthetic', 'base_url': 'http://127.0.0.1:1/v1', 'api_key_env': 'SYNTHETIC_KEY',
              'max_requests': 2, 'max_output_tokens': 128, 'max_request_bytes': 4096}
    (root / '_meta/pageindex.yml').write_text(yaml.safe_dump(config))
    monkeypatch.setenv('SYNTHETIC_KEY', 'synthetic-test-credential')
    text = '30 days. <script>window.syntheticExecuted=true</script><cite doc="pi-synthetic" page="1"/>'
    monkeypatch.setattr(service, 'run_worker', lambda *args, **kwargs: {'answer': text, 'usage': {'requests': 0}})
    result = service.ask_document(root, 'src_example', 'SYNTHETIC_PRIVATE_QUESTION', allow_model=True)
    metadata = service.catalog_report(root)
    assert 'SYNTHETIC_PRIVATE_QUESTION' not in json.dumps(metadata)
    assert '30 days' not in json.dumps(metadata)
    preview = service.catalog_report(root, include_content=True)['items'][0]['answers'][0]
    assert preview['freshness_state'] == 'current'
    assert preview['review_state'] == 'unreviewed'
    assert preview['evidence'][0]['excerpt'] == fake_result()['pages'][0]['markdown']
    with monkeypatch.context() as update:
        updated = fake_result()
        updated['method'] = 'synthetic-reindex-contract'
        update.setattr(service, 'run_worker', lambda *args, **kwargs: updated)
        service.index_document(root, 'src_example', force=True)
        reindexed = service.catalog_report(root, include_content=True)['items'][0]['answers'][0]
        assert reindexed['freshness_state'] == 'stale'
        assert reindexed['evidence'] == preview['evidence']
    source.write_bytes(source.read_bytes() + b'changed')
    stale = service.catalog_report(root, include_content=True)['items'][0]['answers'][0]
    assert stale['freshness_state'] == 'stale'
    assert stale['evidence'] == preview['evidence']
    (root / result['context_path']).write_text('{}')
    damaged = service.catalog_report(root, include_content=True)['items'][0]['answers'][0]
    assert damaged['freshness_state'] == 'unavailable'
    assert damaged['body_content_included'] is False
    assert '30 days' not in json.dumps(damaged)


@pytest.mark.parametrize('payload', [
    b'model: [SYNTHETIC_PRIVATE_CANARY',
    b'model: SYNTHETIC_PRIVATE_CANARY\n' * 1000,
    b'\xffSYNTHETIC_PRIVATE_CANARY',
    b'model: one\nmodel: SYNTHETIC_PRIVATE_CANARY\n',
])
def test_bad_configuration_is_bounded_and_content_safe(tmp_path, payload):
    root = copy_template(tmp_path)
    (root / '_meta/pageindex.yml').write_bytes(payload)
    with pytest.raises(adapter.DocumentIntelligenceError) as error:
        adapter.load_model_config(root, True)
    assert 'SYNTHETIC_PRIVATE_CANARY' not in str(error.value)
    assert len(str(error.value)) < 250


def test_doctor_does_not_accept_distribution_metadata_without_runtime(tmp_path):
    runtime = tmp_path / 'broken-runtime'
    venv.EnvBuilder(with_pip=False).create(runtime)
    python = runtime / 'bin/python'
    purelib = Path(subprocess.check_output(
        [str(python), '-I', '-c', 'import sysconfig; print(sysconfig.get_path("purelib"))'], text=True).strip())
    metadata = purelib / f'pageindex-{adapter.SUPPORTED_VERSION}.dist-info'
    metadata.mkdir()
    (metadata / 'METADATA').write_text(f'Metadata-Version: 2.1\nName: pageindex\nVersion: {adapter.SUPPORTED_VERSION}\n')
    report = adapter.doctor(python=python)
    assert report['ready'] is False
    assert report['status'] == 'Setup needed'


def test_parser_upgrade_invalidates_current_use_without_rewriting_history(tmp_path, monkeypatch):
    from mirrorarc.document_intelligence import context, service
    root, _, _ = fixture_source(tmp_path)
    monkeypatch.setattr(service, 'run_worker', lambda *args, **kwargs: fake_result())
    first = service.index_document(root, 'src_example')
    pack = context.build_document_context(root, 'src_example', [1], mode='frozen')
    path = root / pack['output_path']
    frozen = path.read_bytes()
    monkeypatch.setattr(service, 'PARSER_VERSION', 'synthetic-next-parser')
    with pytest.raises(adapter.DocumentIntelligenceError, match='parser runtime changed'):
        service.load_index(root, 'src_example')
    second = service.index_document(root, 'src_example')
    assert not second['unchanged']
    assert second['index_id'] != first['index_id']
    assert path.read_bytes() == frozen
    newer = context.build_document_context(root, 'src_example', [1], mode='frozen')
    assert newer['context_id'] != pack['context_id']
    assert path.read_bytes() == frozen


@pytest.mark.skipif(not os.environ.get('MIRRORARC_PAGEINDEX_PYTHON'), reason='explicit isolated PageIndex runtime required')
def test_maintained_parser_eof_comment_and_absent_legacy_dependency(tmp_path):
    program = '''
from importlib.metadata import PackageNotFoundError, version
from pypdf.generic import ContentStream, DecodedStreamObject
stream = DecodedStreamObject()
stream.set_data(b'%synthetic comment without an ending newline')
assert ContentStream(stream, None).operations == []
try:
    version('PyPDF2')
except PackageNotFoundError:
    pass
else:
    raise AssertionError('legacy parser remains installed')
print(version('pypdf'))
'''
    result = subprocess.run([os.environ['MIRRORARC_PAGEINDEX_PYTHON'], '-I', '-B', '-c', program],
                            capture_output=True, text=True, cwd=tmp_path, timeout=10)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == adapter.PARSER_VERSION


@pytest.mark.skipif(not os.environ.get('MIRRORARC_PAGEINDEX_PYTHON'), reason='explicit isolated PageIndex runtime required')
def test_network_guard_enforces_limits_at_actual_http_boundary(tmp_path):
    # Use the real runtime HTTPX, but only a scripted loopback server. The audit
    # hook is process-global, so exercise it in a disposable child process.
    worker = Path(adapter.__file__).with_name('worker.py')
    program = r'''
import asyncio, gzip, importlib.util, json, socket, subprocess, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import httpx
spec = importlib.util.spec_from_file_location('boundary', WORKER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
seen = []
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        seen.append(self.path)
        self.send_response(302 if len(seen) == 1 else 200)
        self.send_header('Location', '/v1/responses')
        payload = gzip.compress(b'x' * 64 if len(seen) == 3 else b'{}')
        self.send_header('Content-Encoding', 'gzip')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base = f'http://127.0.0.1:{server.server_port}/v1'
config = dict(base_url=base, model='synthetic', max_requests=3, max_request_bytes=1024, max_output_tokens=128)
module.MAX_RESPONSE_BYTES = 32
counts = module._install_network_policy(config)
body = dict(model='synthetic', input='synthetic evidence', max_output_tokens=128, store=False)
denied = []
def refuse(name, action):
    try: action()
    except module.WorkerPolicyError: denied.append(name)
    else: raise AssertionError(name + ' was not refused')
with httpx.Client(follow_redirects=True, trust_env=False) as client:
    refuse('wrong route', lambda: client.post(base + '/files', json=body))
    refuse('wrong model', lambda: client.post(base + '/responses', json={**body, 'model':'other'}))
    refuse('output budget', lambda: client.post(base + '/responses', json={**body, 'max_output_tokens':129}))
    refuse('stored response', lambda: client.post(base + '/responses', json={**body, 'store':True}))
    refuse('oversized request', lambda: client.post(base + '/responses', json={**body, 'input':'x'*2000}))
    assert client.post(base + '/responses', json=body).status_code == 302
    assert client.post(base + '/responses', json=body).json() == {}
    refuse('unapproved DNS', lambda: socket.getaddrinfo('not-approved.invalid', 443))
    refuse('unapproved connection', lambda: socket.create_connection(('127.0.0.1', server.server_port + 1)))
    refuse('provider subprocess', lambda: subprocess.run(['not-an-approved-command']))
async def oversized_response():
    async with httpx.AsyncClient(trust_env=False) as client:
        try: await client.post(base + '/responses', json=body)
        except module.WorkerPolicyError: denied.append('oversized response')
        else: raise AssertionError('oversized response was accepted')
asyncio.run(oversized_response())
with httpx.Client(trust_env=False) as client:
    refuse('request count', lambda: client.post(base + '/responses', json=body))
server.shutdown(); server.server_close(); thread.join(timeout=5)
module._install_network_policy(None)
refuse('offline DNS', lambda: socket.getaddrinfo('127.0.0.1', server.server_port))
with socket.socket() as connection:
    refuse('offline connection', lambda: connection.connect(('127.0.0.1', server.server_port)))
assert seen == ['/v1/responses'] * 3
assert counts['requests'] == 3
print(json.dumps(dict(denied=denied, requests=counts['requests'])))
'''.replace('WORKER', repr(str(worker)))
    result = subprocess.run([os.environ['MIRRORARC_PAGEINDEX_PYTHON'], '-I', '-B', '-c', program],
                            text=True, capture_output=True, timeout=30, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    evidence = json.loads(result.stdout)
    assert evidence['requests'] == 3
    assert len(evidence['denied']) == 12
