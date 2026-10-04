# SPDX-License-Identifier: AGPL-3.0-or-later
"""Release regressions from the independent review; synthetic records only."""
import json

import pytest
import yaml

from mirrorarc.context_assembly.builder import ContextAssemblyError, build_context, freeze_context, resolve_dynamic_context
from mirrorarc.context_assembly.store import ContextStore
from mirrorarc.code_intelligence.context import build_dynamic_code_context, freeze_code_context
from mirrorarc.code_intelligence.service import analyze_repository
from mirrorarc.relationships.deterministic import refresh
from test_context_assembly import copy_template, add_native_source
from test_code_intelligence import copy_vault, fake_codegraph


@pytest.mark.parametrize('kind', ['document', 'code'])
def test_effective_budget_change_never_rewrites_frozen_history(tmp_path, kind):
    if kind == 'document':
        root = copy_template(tmp_path)
        add_native_source(root, 'source.md', 'Synthetic unchanged evidence.')
        refresh(root)
        definition = build_context(root, 'orientation')['definition']
        freeze = lambda: freeze_context(root, definition_id=definition['definition_id'])
    else:
        root, repo_id = copy_vault(tmp_path)
        analysis = analyze_repository(root, repo_id, symbol='demand_change', binary=fake_codegraph(tmp_path))
        definition = build_dynamic_code_context(root, analysis)['definition']
        freeze = lambda: freeze_code_context(root, analysis, definition=definition)
    first = freeze()
    path = root / first['output_path']
    previous = path.read_bytes()
    profile_path = root / '_meta/profile.yml'
    profile = yaml.safe_load(profile_path.read_text())
    profile['context_defaults']['max_tokens'] -= 1
    profile_path.write_text(yaml.safe_dump(profile, sort_keys=False))
    second = freeze()
    assert second['context_id'] != first['context_id']
    assert path.read_bytes() == previous
    assert freeze()['unchanged']
    # Dropped derived pack records must not change the surviving frozen file.
    second_path = root / second['output_path']
    second_bytes = second_path.read_bytes()
    with ContextStore(root).connect() as connection:
        connection.execute('DELETE FROM context_packs')
    assert freeze()['unchanged']
    assert second_path.read_bytes() == second_bytes
    second_path.write_bytes(second_bytes + b'\n')
    with pytest.raises(ContextAssemblyError, match='refusing to overwrite'):
        freeze()
    assert second_path.read_bytes() == second_bytes + b'\n'


@pytest.mark.parametrize('count', [120, 500])
def test_retrieval_diagnostics_leave_room_for_evidence(tmp_path, count):
    root = copy_template(tmp_path)
    for index in range(count):
        add_native_source(root, f'{index:03d}.md', 'needle evidence' if index == 0 else 'unrelated material')
    result = build_context(root, 'orientation', mode='metadata', query='needle', max_files=2)
    assert len(result['items']) == 1
    definition = build_context(root, 'orientation', query='needle', max_files=2)['definition']
    assert len(resolve_dynamic_context(root, definition['definition_id'])['items']) == 1
    pack = freeze_context(root, definition_id=definition['definition_id'])
    document = json.loads((root / pack['output_path']).read_bytes())
    assert len(document['items']) == 1
    assert 'needle' in document['items'][0]['excerpt']
    diagnostics = document['retrieval']
    assert diagnostics['excluded_count'] == count - 1
    details = json.loads((root / diagnostics['details_path']).read_text())
    assert len(details['exclusions']) == count - 1
    assert len(document['retrieval']['exclusions']) <= 5
    empty = build_context(root, 'orientation', mode='metadata', query='absentword', max_files=2)
    assert empty['items'] == []
