# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded subprocess boundary for the optional pinned PageIndex runtime."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import tempfile
import time
from urllib.parse import urlsplit

import yaml

from mirrorarc.document_intelligence.worker import SUPPORTED_VERSION, PARSER_VERSION, PDFIUM_VERSION

MAX_OUTPUT = 6_000_000


class DocumentIntelligenceError(ValueError):
    """An actionable, content-safe document workflow failure."""


def read_bounded(path: Path, limit: int, label: str) -> bytes:
    """Read one stable regular file without trusting a prior stat/size check."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'rb') as handle:
            before = os.fstat(handle.fileno())
            if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
                raise DocumentIntelligenceError(f'{label} is not a regular file within its byte limit')
            payload = handle.read(limit + 1)
            after = os.fstat(handle.fileno())
        fingerprint = lambda item: (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns, item.st_ctime_ns)
        if len(payload) > limit or len(payload) != after.st_size or fingerprint(before) != fingerprint(after):
            raise DocumentIntelligenceError(f'{label} changed while reading or exceeds its byte limit')
        return payload
    except OSError:
        raise DocumentIntelligenceError(f'{label} is missing, unreadable or not a regular file') from None


class _UniqueConfigLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in result:
                raise ValueError('duplicate configuration key')
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def load_model_config(root: Path, allow_model: bool) -> dict:
    if not allow_model:
        raise DocumentIntelligenceError('Model use is opt-in; review _meta/pageindex.yml and pass --allow-model explicitly.')
    path = root / '_meta/pageindex.yml'
    if path.is_symlink() or not path.is_file() or (root / '_meta').is_symlink():
        raise DocumentIntelligenceError('Create a local _meta/pageindex.yml with the approved model and endpoint; never put a key in it.')
    try:
        config = yaml.load(read_bounded(path, 16384, 'Model configuration').decode('utf-8'), Loader=_UniqueConfigLoader)
    except (yaml.YAMLError, ValueError, TypeError, RecursionError):
        raise DocumentIntelligenceError('Model configuration is invalid, duplicated or oversized; check _meta/pageindex.yml without storing credentials.') from None
    keys = {'model', 'base_url', 'api_key_env', 'max_requests', 'max_output_tokens', 'max_request_bytes'}
    if not isinstance(config, dict) or set(config) != keys:
        raise DocumentIntelligenceError('PageIndex model configuration must contain exactly: ' + ', '.join(sorted(keys)))
    if not isinstance(config['model'], str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,120}', config['model']):
        raise DocumentIntelligenceError('Use a bare model ID for the approved OpenAI-compatible endpoint.')
    if not isinstance(config['base_url'], str):
        raise DocumentIntelligenceError('base_url must be an explicit API URL')
    try:
        endpoint = urlsplit(config['base_url'])
        port = endpoint.port
    except ValueError:
        raise DocumentIntelligenceError('base_url must have a valid hostname and port') from None
    if (endpoint.username or endpoint.password or endpoint.query or endpoint.fragment or not endpoint.hostname
            or len(config['base_url']) > 2048 or any(char.isspace() for char in config['base_url'])
            or port == 0 or '%' in endpoint.path or '\\' in config['base_url']
            or any(part in {'.', '..'} for part in endpoint.path.split('/'))
            or endpoint.scheme not in {'https', 'http'}
            or (endpoint.scheme == 'http' and endpoint.hostname not in {'127.0.0.1', 'localhost', '::1'})):
        raise DocumentIntelligenceError('Use HTTPS, or HTTP on loopback, without credentials, query strings or fragments.')
    if not isinstance(config['api_key_env'], str) or not re.fullmatch(r'[A-Z][A-Z0-9_]{0,100}', config['api_key_env']):
        raise DocumentIntelligenceError('api_key_env must name an environment variable, not contain a key.')
    for key, low, high in [('max_requests', 1, 32), ('max_output_tokens', 128, 4096), ('max_request_bytes', 1024, 500_000)]:
        if type(config[key]) is not int or not low <= config[key] <= high:
            raise DocumentIntelligenceError(f'{key} must be an integer from {low} to {high}')
    if not os.environ.get(config['api_key_env']):
        raise DocumentIntelligenceError('The configured credential environment variable is not set.')
    return config


def run_worker(request: dict, *, python: str | Path | None = None, timeout: float = 180) -> dict:
    runtime = python or os.environ.get('MIRRORARC_PAGEINDEX_PYTHON')
    if not runtime or not Path(runtime).expanduser().is_file():
        raise DocumentIntelligenceError(f'Setup needed: follow docs/PAGEINDEX.md, then set MIRRORARC_PAGEINDEX_PYTHON to the isolated patched PageIndex {SUPPORTED_VERSION} runtime.')
    # Never inherit arbitrary provider credentials, proxies, Python paths or .env.
    environment = {key: os.environ[key] for key in ('PATH', 'SYSTEMROOT', 'TMPDIR', 'SSL_CERT_FILE', 'SSL_CERT_DIR') if key in os.environ}
    environment.update(PYTHON_DOTENV_DISABLED='1', OPENAI_AGENTS_DISABLE_TRACING='1',
                       LITELLM_LOCAL_MODEL_COST_MAP='True', DO_NOT_TRACK='1',
                       HF_HUB_OFFLINE='1', TOKENIZERS_PARALLELISM='false')
    config = request.get('model_config')
    if config:
        credential = os.environ.get(config['api_key_env'])
        if not credential:
            raise DocumentIntelligenceError('The configured credential environment variable is not set.')
        environment['MIRRORARC_MODEL_KEY'] = credential
    with tempfile.TemporaryDirectory(prefix='mirrorarc-pageindex-') as scratch:
        environment['XDG_CACHE_HOME'] = scratch
        path = Path(scratch) / 'request.json'
        path.write_text(json.dumps(request, ensure_ascii=False))
        os.chmod(path, 0o600)
        command = [str(Path(runtime).expanduser().absolute()), '-I', '-B', str(Path(__file__).with_name('worker.py')), str(path)]
        buffers = {'stdout': bytearray(), 'stderr': bytearray()}
        try:
            with subprocess.Popen(command, cwd=scratch, env=environment, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, start_new_session=True) as child:
                deadline = time.monotonic() + timeout
                try:
                    with selectors.DefaultSelector() as selector:
                        selector.register(child.stdout, selectors.EVENT_READ, 'stdout')
                        selector.register(child.stderr, selectors.EVENT_READ, 'stderr')
                        while selector.get_map():
                            remaining = deadline - time.monotonic()
                            if remaining <= 0:
                                raise DocumentIntelligenceError('PageIndex timed out; no new result was published.')
                            for key, _ in selector.select(min(remaining, 0.1)):
                                chunk = os.read(key.fd, 65536)
                                if not chunk:
                                    selector.unregister(key.fileobj)
                                    continue
                                buffers[key.data].extend(chunk)
                                if len(buffers[key.data]) > MAX_OUTPUT:
                                    raise DocumentIntelligenceError('PageIndex output exceeded the safety limit.')
                    child.wait(timeout=max(0.001, deadline - time.monotonic()))
                finally:
                    try:
                        os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    child.wait()
            value = json.loads(buffers['stdout'])
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            if isinstance(exc, DocumentIntelligenceError):
                raise
            raise DocumentIntelligenceError('PageIndex worker did not return a valid result; check the isolated runtime.') from exc
        if not isinstance(value, dict) or not value.get('ok') or child.returncode:
            raise DocumentIntelligenceError(value.get('error', 'PageIndex failed') if isinstance(value, dict) else 'PageIndex failed')
        return value['result']


def doctor(*, python: str | Path | None = None) -> dict:
    try:
        return {'status': 'Ready', **run_worker({'action': 'doctor'}, python=python, timeout=20),
                'next_action': 'Index one registered PDF with document index --source <source-id>. Model use is separate and opt-in.'}
    except DocumentIntelligenceError as exc:
        return {'status': 'Setup needed', 'ready': False, 'provider': 'PageIndex',
                'version': SUPPORTED_VERSION, 'next_action': str(exc)}
