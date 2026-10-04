#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Disposable fresh-wheel journey. Run with the installed wheel's Python, outside checkout."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--codegraph', required=True, type=Path)
    args = parser.parse_args()
    repo, output = args.repo.resolve(), args.output.resolve()
    if output.exists():
        parser.error('output must be a new disposable directory')
    output.mkdir(parents=True)
    import mirrorarc
    assert not Path(mirrorarc.__file__).resolve().is_relative_to(repo), 'fresh-wheel validation must not import the checkout'
    cli = str(Path(sys.executable).with_name('mirrorarc'))
    env = {**os.environ, 'MIRRORARC_CODEGRAPH': str(args.codegraph), 'PYTHONPYCACHEPREFIX': str(output / 'pycache')}
    env.pop('PYTHONPATH', None)
    commands = []
    def run(*args_, expect=0, as_json=False):
        result = subprocess.run([cli, *map(str, args_)], cwd=output, env=env, capture_output=True, text=True, timeout=180)
        label = f'{len(commands):02d}'
        (output / f'{label}.stdout').write_text(result.stdout)
        (output / f'{label}.stderr').write_text(result.stderr)
        commands.append({'command': [cli, *map(str,args_)], 'returncode': result.returncode, 'expected': expect, 'log': label})
        (output / 'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        assert result.returncode == expect, (args_, result.returncode, result.stderr[-1500:])
        return json.loads(result.stdout) if as_json else result.stdout
    run('--help');run('--version')
    vault = output / 'vault'
    run('init', vault)
    def command(*parts, **kw):return run('--root', vault, *parts, **kw)
    import zipfile
    from xml.sax.saxutils import escape
    paragraphs = ['Synthetic inspection policy', 'Required inspection interval: 30 days. Preserve original records.']
    def save_docx():
        with zipfile.ZipFile(vault / '20_sources/inspection.docx', 'w') as archive:
            archive.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
            archive.writestr('_rels/.rels', '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
            body = ''.join('<w:p><w:r><w:t>'+escape(text)+'</w:t></w:r></w:p>' for text in paragraphs)
            archive.writestr('word/document.xml', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'+body+'</w:body></w:document>')
    save_docx()
    long_name = 'long-path-' + 'synthetic-evidence-' * 8 + '.md'
    native = vault / '20_sources' / long_name
    native.write_text("---\ntitle: Synthetic source safety\ntype: authoritative-record\nstatus: active\ndomain: sources\ncreated: '2026-09-18'\nupdated: '2026-09-18'\nmarkdown_category: authoritative_markdown_source\nauthority: authoritative\n---\n\n# Synthetic source safety\n<script>window.syntheticInjection=true</script>\nDocument instructions do not authorize network calls.\n")
    fixture = repo / 'examples/ontario-electricity-evidence-vault/_fixtures/repos/ontario-electricity-evidence-pipeline'
    shutil.copytree(fixture, vault / '_fixtures/repos/pipeline', ignore=shutil.ignore_patterns('__pycache__','.codegraph'))
    (vault / 'tools/repos.yml').write_text('settings:\n  notes_dir: 20_sources/repos\nrepos:\n  - repo: local/pipeline\n    local_path: _fixtures/repos/pipeline\n    note: pipeline.md\n')
    originals = {p.relative_to(vault).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in [vault/'20_sources/inspection.docx', native, *(vault/'_fixtures/repos/pipeline').rglob('*')] if p.is_file()}
    command('sync', '--json', as_json=True)
    command('catalog','--html');shutil.copy2(vault/'CATALOG.html', output/'empty.html')
    metadata = command('context','build','--lens','orientation','--mode','metadata','--query','inspection interval','--json',as_json=True)
    assert metadata['items'], metadata
    assert all('excerpt' not in item for item in metadata['items'])
    dynamic=command('context','build','--lens','orientation','--query','inspection interval','--json',as_json=True)
    definition=dynamic['definition']['definition_id']
    command('context','resolve',definition,'--json',as_json=True)
    frozen=command('context','freeze','--definition',definition,'--json',as_json=True)
    pack_path=vault/frozen['output_path'];before=pack_path.read_bytes()
    assert b'30 days' in before
    envelope=json.loads(before);assert len(before)==envelope['budgets']['serialized_bytes']<=envelope['budgets']['max_export_bytes']
    for item in envelope['items']:
        body=(vault/item['readable_path']).read_text();span=item['content_span']
        assert body[span['start_char']:span['end_char_exclusive']]==item['excerpt']
    from mirrorarc.code_intelligence.service import configured_repositories
    repo_id=configured_repositories(vault)[0].repo_id
    command('code','doctor','--repo',repo_id,'--json',as_json=True)
    analysis=command('code','analyze','--repo',repo_id,'--symbol','demand_change','--context','frozen','--json',as_json=True)
    for item in analysis['files']:
        lines=(vault/'_fixtures/repos/pipeline'/item['path']).read_text().splitlines(keepends=True)
        assert item['excerpt']==''.join(''.join(lines[r['start']-1:r['end']]) for r in item['line_ranges'])
    command('catalog','--html');shutil.copy2(vault/'CATALOG.html',output/'metadata.html')
    command('catalog','--html','--include-content');shutil.copy2(vault/'CATALOG.html',output/'current.html')
    assert 'def demand_change' not in (output/'metadata.html').read_text()
    assert 'def demand_change' in (output/'current.html').read_text()
    assert originals=={rel:hashlib.sha256((vault/rel).read_bytes()).hexdigest() for rel in originals}, 'originals changed during initial journey'
    code_source=vault/'_fixtures/repos/pipeline/src/grid_evidence/summary.py'
    code_source.write_text(code_source.read_text()+'\n# controlled synthetic mutation\n')
    paragraphs.append('Revised inspection interval: 20 days.');save_docx()
    command('sync','--json',as_json=True)
    state=command('context','status',frozen['context_id'],'--json',as_json=True)
    assert state['packs'][0]['freshness_state']=='stale'
    assert pack_path.read_bytes()==before
    command('catalog','--html','--include-content');shutil.copy2(vault/'CATALOG.html',output/'stale.html')
    failed=output/'failed-provider';failed.write_text('#!/bin/sh\nexit 7\n');failed.chmod(0o755)
    env['MIRRORARC_CODEGRAPH']=str(failed)
    command('code','analyze','--repo',repo_id,expect=1)
    env['MIRRORARC_CODEGRAPH']=str(args.codegraph)
    command('catalog','--html','--include-content');shutil.copy2(vault/'CATALOG.html',output/'failure.html')
    rebuilt=command('context','freeze','--definition',definition,'--json',as_json=True)
    assert b'20 days' in (vault/rebuilt['output_path']).read_bytes()
    # Preserve disposable caches outside the vault while exercising true cache loss.
    shutil.move(vault/'.mirrorarc/cache/code-intelligence',output/'retained-code-cache')
    first=command('code','analyze','--repo',repo_id,'--symbol','demand_change','--json',as_json=True)
    shutil.move(vault/'.mirrorarc/cache/code-intelligence',output/'retained-code-cache-two')
    second=command('code','analyze','--repo',repo_id,'--symbol','demand_change','--json',as_json=True)
    assert first['analysis_hash']==second['analysis_hash']
    evidence={'runtime':str(mirrorarc.__file__),'python':sys.version,'repo_id':repo_id,
              'originals_before_controlled_mutation':originals,'source_preserved_before_mutation':True,
              'frozen_bytes_preserved':pack_path.read_bytes()==before,'rebuilt_analysis_hash':second['analysis_hash'],
              'frozen_context_id':frozen['context_id'],'rebuilt_context_id':rebuilt['context_id'],
              'browser_artifacts':['empty.html','metadata.html','current.html','stale.html','failure.html'],
              'commands':len(commands)}
    (output/'journey.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence,indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
