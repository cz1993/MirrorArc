# SPDX-License-Identifier: AGPL-3.0-or-later
"""Answer contract, frozen history and Catalog exclusion checks; no model-quality claim."""
import hashlib
import json

import pytest

from mirrorarc.document_intelligence import service
from mirrorarc.document_intelligence.presentation import CONTRACT, read_presentation
from mirrorarc.relationships.model import stable_id
from test_document_intelligence import fixture_source, fake_result

CITE = '<cite doc="pi-synthetic" page="1"/>'
ANSWER = f'''Answer:
30 days. {CITE}
Reason:
The fictional schedule specifies the interval. {CITE}
Important:
<script>window.syntheticExecuted=true</script> Conflicting evidence needs review.
Details:
Additional evidence remains available. {CITE}'''


def publish(tmp_path, monkeypatch, answer=ANSWER):
    root, source, _ = fixture_source(tmp_path)
    monkeypatch.setattr(service, 'run_worker', lambda *a, **k: fake_result())
    service.index_document(root, 'src_example')
    monkeypatch.setattr(service, 'load_model_config', lambda *a: {'model': 'synthetic', 'base_url': 'https://example.invalid'})
    def respond(request, **kwargs):
        assert 'prior answer that matched' in request['answer_instructions']
        return {'answer': answer, 'usage': {}}
    monkeypatch.setattr(service, 'run_worker', respond)
    result = service.ask_document(root, 'src_example', 'Synthetic question?', allow_model=True)
    return root, source, result


def test_answer_first_preserves_original_and_frozen_history(tmp_path, monkeypatch):
    root, source, record = publish(tmp_path, monkeypatch)
    original = (root / record['output_path']).read_bytes()
    frozen = (root / record['context_path']).read_bytes()
    preview = service.catalog_report(root, include_content=True)['items'][0]['answers'][0]
    assert record['presentation_contract'] == CONTRACT
    assert record['answer'] == preview['original_answer'] == ANSWER
    assert preview['presentation']['state'] == 'structured'
    assert preview['presentation']['sections']['reason'][1] == {'page': 1}
    assert '<script>' in preview['presentation']['sections']['important'][0]['text']
    assert preview['evidence'][0]['excerpt'] == fake_result()['pages'][0]['markdown']
    source.write_bytes(source.read_bytes() + b'changed')
    stale = service.catalog_report(root, include_content=True)['items'][0]['answers'][0]
    assert stale['freshness_state'] == 'stale'
    assert stale['presentation'] == preview['presentation']
    assert (root / record['output_path']).read_bytes() == original
    assert (root / record['context_path']).read_bytes() == frozen
    (root / record['context_path']).write_bytes(frozen + b' ')
    unavailable = service.catalog_report(root, include_content=True)['items'][0]['answers'][0]
    assert unavailable['freshness_state'] == 'unavailable'
    assert 'original_answer' not in unavailable


def test_old_record_and_metadata_exclusion(tmp_path, monkeypatch):
    root, _, record = publish(tmp_path, monkeypatch)
    path = root / record['output_path']
    old = json.loads(path.read_text())
    del old['presentation_contract']
    del old['answer_id']
    old['answer_id'] = stable_id('answer', service._digest(old))
    path.unlink()
    (path.parent / (old['answer_id'] + '.json')).write_text(json.dumps(old))
    preview = service.catalog_report(root, include_content=True)['items'][0]['answers'][0]
    assert preview['presentation']['state'] == 'original'
    assert preview['original_answer'] == ANSWER
    metadata = json.dumps(service.catalog_report(root))
    for text in ['Synthetic question?', '30 days.', 'Conflicting evidence', 'presentation', 'original_answer']:
        assert text not in metadata
    items, remaining = service._answer_previews(root, service.status_report(root)['items'][0], True, 1)
    assert remaining == 1 and not items[0]['body_content_included']
    assert 'original_answer' not in items[0]


@pytest.mark.parametrize('text,contract', [
    (ANSWER, None), (ANSWER, 'future'), ('Unstructured ' + CITE, CONTRACT),
    ('prefix\n' + ANSWER, CONTRACT), (ANSWER.replace('Important:', 'Warnings:'), CONTRACT),
    (ANSWER + '\nReason:\nDuplicated', CONTRACT),
    (ANSWER.replace('Reason:\nThe fictional schedule specifies the interval. ' + CITE, 'Reason:\nNo citation'), CONTRACT),
    (ANSWER.replace('page="1"', 'page="999"'), CONTRACT),
    (ANSWER.replace('Important:\n', 'Important:\n<cite broken>'), CONTRACT),
    (ANSWER.replace('<script>window.syntheticExecuted=true</script> Conflicting evidence needs review.', ''), CONTRACT),
])
def test_unreadable_contract_is_never_guessed(text, contract):
    value = read_presentation(text, contract, [{'page': 1}])
    assert value['state'] == 'original'
    assert 'complete original' in value['warning']


def test_catalog_renderer_uses_text_escaping_and_passive_citation_disclosure():
    from mirrorarc import catalog_explorer
    code = __import__('inspect').getsource(catalog_explorer)
    assert 'escapeHtml(part.text)' in code
    assert 'escapeHtml(answer.original_answer)' in code
    assert 'evidence.querySelector("summary").focus()' in code
    assert 'Unreviewed answer candidate' in code
    assert 'Complete original generated answer' in code
