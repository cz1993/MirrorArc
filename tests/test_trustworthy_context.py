# SPDX-License-Identifier: AGPL-3.0-or-later
"""Public boundary regressions for the Trustworthy Context batch (synthetic only)."""
import hashlib
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path

import pytest
import yaml

from mirrorarc.cli import main
from mirrorarc.code_intelligence.adapter import CodeGraphAdapter, CodeGraphError
from mirrorarc.code_intelligence.service import analyze_repository, catalog_report, CACHE_ROOT, CodeIntelligenceError
from mirrorarc.context_assembly.builder import build_context, freeze_context, ContextAssemblyError
from mirrorarc.relationships.deterministic import refresh
from test_code_intelligence import copy_vault, fake_codegraph
from test_context_assembly import copy_template, add_native_source


def restrict(vault, modes):
    path = vault / '_meta/profile.yml'
    profile = yaml.safe_load(path.read_text())
    profile['context_defaults']['allowed_modes'] = modes
    path.write_text(yaml.safe_dump(profile, sort_keys=False))


def test_denied_context_cli_has_no_cache_or_database_side_effects(tmp_path, capsys):
    vault, repo_id = copy_vault(tmp_path)
    restrict(vault, ['metadata'])
    for args in [
        ['context', 'freeze', '--lens', 'orientation'],
        ['context', 'build', '--lens', 'orientation', '--mode', 'dynamic'],
        ['context', 'resolve', 'missing-definition'],
        ['code', 'analyze', '--repo', repo_id, '--context', 'frozen'],
        ['code', 'analyze', '--repo', repo_id, '--context', 'dynamic'],
    ]:
        assert main(['--root', str(vault), *args]) == 1
        assert 'allow' in capsys.readouterr().err
        assert not (vault / '.mirrorarc').exists()


def test_revoked_policy_blocks_saved_definition_freeze(tmp_path):
    vault = copy_template(tmp_path)
    add_native_source(vault, 'source.md', 'Synthetic source')
    refresh(vault)
    definition = build_context(vault, 'orientation')['definition']['definition_id']
    restrict(vault, ['metadata'])
    before = {p: p.read_bytes() for p in (vault / '.mirrorarc').rglob('*') if p.is_file()}
    with pytest.raises(ContextAssemblyError, match='not allowed'):
        freeze_context(vault, definition_id=definition)
    assert before == {p: p.read_bytes() for p in (vault / '.mirrorarc').rglob('*') if p.is_file()}


def test_code_public_cli_exact_union_and_catalog_selection(tmp_path, monkeypatch, capsys):
    vault, repo_id = copy_vault(tmp_path)
    monkeypatch.setenv('MIRRORARC_CODEGRAPH', str(fake_codegraph(tmp_path)))
    assert main(['--root', str(vault), 'code', 'analyze', '--repo', repo_id,
                 '--symbol', 'demand_change', '--changed-path', 'src/grid_evidence/summary.py', '--json']) == 0
    result = json.loads(capsys.readouterr().out)
    for item in result['files']:
        source = vault / '_fixtures/repos/pipeline' / item['path']
        lines = source.read_text().splitlines(keepends=True)
        expected = ''.join(''.join(lines[r['start']-1:r['end']]) for r in item['line_ranges'])
        assert item['excerpt'] == expected
        assert hashlib.sha256(expected.encode()).hexdigest() == item['excerpt_hash']
    action = catalog_report(vault)['repositories'][0]['context_command']
    assert '--symbol=demand_change' in shlex.split(action)
    assert '--changed-path=src/grid_evidence/summary.py' in shlex.split(action)


def test_snapshot_tamper_and_copy_race_fail_closed(tmp_path, monkeypatch):
    import mirrorarc.code_intelligence.service as service
    vault, repo_id = copy_vault(tmp_path)
    binary = fake_codegraph(tmp_path)
    first = analyze_repository(vault, repo_id, symbol='demand_change', binary=binary)
    snapshot = next((vault / CACHE_ROOT).glob('*/snapshots/*/source'))
    (snapshot / 'src/grid_evidence/summary.py').write_text('tampered synthetic snapshot\n')
    with pytest.raises(CodeIntelligenceError, match='Snapshot identity mismatch'):
        analyze_repository(vault, repo_id, symbol='demand_change', binary=binary)
    assert first['analysis_id'] in (vault / CACHE_ROOT / repo_id / 'latest.json').read_text()

    # A separate fresh source identity lets one controlled mutation exercise copying.
    source = vault / '_fixtures/repos/pipeline/src/grid_evidence/summary.py'
    source.write_text(source.read_text() + '\n# new synthetic revision\n')
    original = service.shutil.copy2
    def racing_copy(src, dst, *args, **kwargs):
        result = original(src, dst, *args, **kwargs)
        if Path(src) == source:
            source.write_text(source.read_text() + '# changed during copy\n')
        return result
    monkeypatch.setattr(service.shutil, 'copy2', racing_copy)
    with pytest.raises(CodeIntelligenceError, match='Snapshot identity mismatch'):
        analyze_repository(vault, repo_id, binary=binary)


@pytest.mark.parametrize('behavior,kind', [
    ("import os\nwhile True: os.write(1, b'x'*8192)", 'provider-output-limit'),
    ("import os\nwhile True: os.write(2, b'x'*8192)", 'provider-output-limit'),
    ("import time\ntime.sleep(30)", 'provider-timeout'),
])
def test_provider_stream_limits_and_timeout(tmp_path, behavior, kind):
    binary = tmp_path / 'bounded-provider'
    binary.write_text(f'#!{sys.executable}\n' + behavior + '\n')
    binary.chmod(0o755)
    start = time.monotonic()
    with pytest.raises(CodeGraphError) as failure:
        CodeGraphAdapter(binary, timeout_seconds=2, output_limit=10000).version()
    assert failure.value.kind == kind
    assert time.monotonic() - start < 5


def test_base_tracks_staged_unstaged_untracked_and_deleted_paths(tmp_path, monkeypatch):
    vault, repo_id = copy_vault(tmp_path)
    source = vault / '_fixtures/repos/pipeline'
    def git(*args):
        return subprocess.run(['git', '-C', str(source), *args], check=True, capture_output=True)
    git('init'); git('add', '.')
    git('-c', 'user.name=Synthetic Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'synthetic baseline')
    git('mv', 'README.md', 'renamed file.md')
    (source / 'src/grid_evidence/summary.py').write_text((source / 'src/grid_evidence/summary.py').read_text() + '\n# working tree\n')
    (source / '-option like.txt').write_text('synthetic untracked\n')
    result = analyze_repository(vault, repo_id, base='HEAD', binary=fake_codegraph(tmp_path))
    assert set(result['request']['resolved_changed_paths']) == {'README.md', 'renamed file.md', 'src/grid_evidence/summary.py', '-option like.txt'}
    assert any('README.md' in omission for omission in result['omissions'])
    assert all(item['path'] != 'README.md' for item in result['files'])


def test_final_unicode_export_bytes_and_exact_character_spans(tmp_path):
    vault = copy_template(tmp_path)
    for i in range(4):
        add_native_source(vault, f'unicode-{i}.md', '雪🌈 café\n' * 400)
    refresh(vault)
    result = freeze_context(vault, lens_id='orientation', max_tokens=2000, max_excerpt_chars=700)
    payload = (vault / result['output_path']).read_bytes()
    assert len(payload) <= 8000
    doc = json.loads(payload)
    assert len(payload) == doc['budgets']['serialized_bytes']
    assert doc['offline_complete'] is False
    assert doc['omissions']
    for item in doc['items']:
        source = (vault / item['readable_path']).read_text()
        span = item['content_span']
        assert source[span['start_char']:span['end_char_exclusive']] == item['excerpt']
    with pytest.raises(ContextAssemblyError, match='overhead exceeds'):
        freeze_context(vault, lens_id='orientation', max_tokens=1)


def test_task_changes_frozen_identity_without_overwriting(tmp_path):
    vault = copy_template(tmp_path)
    add_native_source(vault, 'source.md', 'Synthetic task evidence')
    refresh(vault)
    first = freeze_context(vault, lens_id='orientation', task='Task one')
    before = (vault / first['output_path']).read_bytes()
    second = freeze_context(vault, lens_id='orientation', task='Task two')
    assert first['context_id'] != second['context_id']
    assert (vault / first['output_path']).read_bytes() == before


def test_query_cli_is_stable_rebuildable_and_checks_live_hashes(tmp_path, capsys):
    from mirrorarc.relationships.store import RelationshipStore
    vault = copy_template(tmp_path)
    source = add_native_source(vault, 'match.md', '# Target\nRarequartz evidence.\n')
    add_native_source(vault, 'other.md', 'Unrelated synthetic record.\n')
    refresh(vault)
    args = ['--root', str(vault), 'context', 'build', '--lens', 'orientation', '--mode', 'metadata', '--query', 'rarequartz', '--json']
    assert main(args) == 0
    first = json.loads(capsys.readouterr().out)
    assert len(first['items']) == 1
    assert first['items'][0]['source_path'].endswith('match.md')
    with RelationshipStore(vault).connect() as conn:
        conn.execute('DROP TABLE context_search')
    assert main(args) == 0
    rebuilt = json.loads(capsys.readouterr().out)
    assert rebuilt['items'] == first['items']
    source.write_text(source.read_text().replace('Rarequartz', 'Different'))
    assert main(args) == 0
    stale = json.loads(capsys.readouterr().out)
    assert stale['items'] == []
    assert all('excerpt' not in item for item in stale['items'])
    refresh(vault)
    assert main(args) == 0
    assert json.loads(capsys.readouterr().out)['items'] == []
    source.unlink()
    refresh(vault)
    assert main(args) == 0
    assert json.loads(capsys.readouterr().out)['items'] == []


def test_query_never_expands_proposed_rejected_or_stale_edges(tmp_path):
    from mirrorarc.relationships.store import RelationshipStore
    from mirrorarc.relationships.proposals import propose
    vault = copy_template(tmp_path)
    add_native_source(vault, 'alpha.md', 'Rarequartz seed evidence.\n')
    second = add_native_source(vault, 'beta.md', 'Unrelated supporting record.\n')
    profile_path = vault / '_meta/profile.yml'
    profile = yaml.safe_load(profile_path.read_text())
    profile['knowledge_lenses']['orientation']['relationship_types'].append('SUPPORTS')
    profile_path.write_text(yaml.safe_dump(profile))
    refresh(vault)
    store = RelationshipStore(vault)
    artifacts = {a['path']: a for a in store.export()['artifacts'] if a['artifact_kind'] == 'native-source'}
    a, b = artifacts['20_sources/alpha.md'], artifacts['20_sources/beta.md']
    relation = propose(vault, source_artifact_id=a['artifact_id'], target_artifact_id=b['artifact_id'],
                       relationship_type='SUPPORTS', evidence_artifact_id=a['artifact_id'],
                       selector_type='line', selector_value='13', excerpt='Rarequartz seed evidence.',
                       confidence=0.8, method='synthetic-proposal', method_version='1')
    def selected():
        return build_context(vault, 'orientation', mode='metadata', query='rarequartz')['items']
    assert len(selected()) == 1
    store.review_relationship(relation['relationship_id'], reviewer='synthetic-reviewer', verdict='accepted')
    assert len(selected()) == 2
    store.review_relationship(relation['relationship_id'], reviewer='synthetic-reviewer', verdict='rejected')
    assert len(selected()) == 1


def test_compact_benchmark_preserves_manifest_and_has_no_model_grades():
    from mirrorarc.benchmark import run_compact_pack
    pack = Path(__file__).parent / 'fixtures/trustworthy_context/pack.json'
    result = run_compact_pack(pack, task_retrieval=True)
    assert len(result['results']) == 12
    assert sum(r['split'] == 'held-out' for r in result['results']) == 3
    assert all(r['model_correctness_score'] is None for r in result['results'])
    assert 'pending' in result['empirical_model_evaluation']


def test_first_query_build_refreshes_existing_source_authority(tmp_path):
    vault = copy_template(tmp_path)
    add_native_source(vault, 'first.md', 'Rarequartz first-use evidence.')
    # No explicit relationship-refresh prerequisite for the task journey.
    result = build_context(vault, 'orientation', mode='metadata', query='rarequartz')
    assert len(result['items']) == 1


def test_public_code_disjoint_spans_and_option_like_selection(tmp_path, monkeypatch, capsys):
    vault, repo_id = copy_vault(tmp_path)
    monkeypatch.setenv('MIRRORARC_CODEGRAPH', str(fake_codegraph(tmp_path)))
    assert main(['--root', str(vault), 'code', 'analyze', '--repo', repo_id,
                 '--symbol', 'demand_change', '--changed-path=-option like.py', '--json']) == 0
    result = json.loads(capsys.readouterr().out)
    for item in result['files']:
        lines = (vault / '_fixtures/repos/pipeline' / item['path']).read_text().splitlines(keepends=True)
        assert item['excerpt'] == ''.join(''.join(lines[r['start']-1:r['end']]) for r in item['line_ranges'])
    command = shlex.split(catalog_report(vault)['repositories'][0]['context_command'])
    assert '--changed-path=-option like.py' in command
    assert '--symbol=demand_change' in command
    with pytest.raises(CodeIntelligenceError, match='unsafe'):
        analyze_repository(vault, repo_id, changed_paths=['../outside.py'], binary=fake_codegraph(tmp_path))


def test_full_sync_invalidates_frozen_opaque_context(tmp_path, capsys):
    vault = copy_template(tmp_path)
    source = vault / '20_sources/inspection.docx'
    import zipfile
    def write_source(days):
        with zipfile.ZipFile(source, 'w') as archive:
            archive.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
            archive.writestr('_rels/.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
            archive.writestr('word/document.xml', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>synthetic interval: '+days+' days</w:t></w:r></w:p></w:body></w:document>')
    write_source('30')
    assert main(['--root', str(vault), 'sync', '--json']) == 0
    capsys.readouterr()
    frozen = freeze_context(vault, lens_id='orientation', query='synthetic interval')
    path = vault / frozen['output_path']
    original = path.read_bytes()
    assert b'30 days' in original
    write_source('20')
    assert main(['--root', str(vault), 'sync', '--json']) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['derived_invalidation']['repaired'] == 1
    assert main(['--root', str(vault), 'context', 'status', frozen['context_id'], '--json']) == 0
    state = json.loads(capsys.readouterr().out)
    assert state['packs'][0]['freshness_state'] == 'stale'
    assert path.read_bytes() == original
    rebuilt = freeze_context(vault, lens_id='orientation', query='synthetic interval')
    assert b'20 days' in (vault / rebuilt['output_path']).read_bytes()
    assert rebuilt['context_id'] != frozen['context_id']


def test_dynamic_code_metadata_reports_complete_export_budget(tmp_path, monkeypatch, capsys):
    from mirrorarc.context_assembly.export import serialize
    vault, repo_id = copy_vault(tmp_path)
    monkeypatch.setenv('MIRRORARC_CODEGRAPH', str(fake_codegraph(tmp_path)))
    assert main(['--root', str(vault), 'code', 'analyze', '--repo', repo_id,
                 '--symbol', 'demand_change', '--context', 'dynamic', '--json']) == 0
    output = json.loads(capsys.readouterr().out)
    resolved = output['context']['resolved']
    assert len(serialize(resolved)) == resolved['budgets']['serialized_bytes']
    assert len(serialize(resolved)) <= resolved['budgets']['max_export_bytes']
    assert all('excerpt' not in item for item in resolved['files'])


def test_catalog_frozen_code_status_uses_live_repository_freshness(tmp_path, monkeypatch, capsys):
    from mirrorarc.catalog import knowledge_projection_report
    vault, repo_id = copy_vault(tmp_path)
    monkeypatch.setenv('MIRRORARC_CODEGRAPH', str(fake_codegraph(tmp_path)))
    assert main(['--root', str(vault), 'code', 'analyze', '--repo', repo_id,
                 '--symbol', 'demand_change', '--context', 'frozen', '--json']) == 0
    capsys.readouterr()
    initial = knowledge_projection_report(vault)['context_packs']
    assert initial and initial[0]['freshness_state'] == 'current'
    source = vault / '_fixtures/repos/pipeline/src/grid_evidence/summary.py'
    source.write_text(source.read_text() + '\n# synthetic change\n')
    packs = knowledge_projection_report(vault)['context_packs']
    assert packs[0]['freshness_state'] == 'stale'
