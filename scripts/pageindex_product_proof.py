# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build a synthetic PDF and exercise the actual optional PageIndex runtime locally.

Run with a Python containing reportlab and MirrorArc, and Poppler's pdftoppm on PATH.
--output must be a new,
durable private directory. No model, credentials or external-source content used.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import html
import io
import json
from pathlib import Path
import shutil
import subprocess

from reportlab.pdfgen import canvas
from mirrorarc.document_intelligence.adapter import doctor
from mirrorarc.document_intelligence.service import index_document, load_index, status_report
from mirrorarc.relationships.deterministic import refresh
from mirrorarc.mirrors import office
from mirrorarc import catalog
from mirrorarc.document_intelligence.context import build_document_context
from mirrorarc.context_assembly.store import ContextStore


def synthetic_pdf(path: Path, interval: int = 30):
    pdf = canvas.Canvas(str(path), pagesize=(612, 792), invariant=True)
    pdf.setTitle('Synthetic equipment inspection guide')
    pdf.setAuthor('Fictional example authored for MirrorArc tests')
    for number, title, lines in [
        (1, '1 Overview', ['This fictional guide defines the inspection interval for a sample pump.',
                           'The pump is not a real product. This document is not operating advice.']),
        (2, '2 Inspection interval', [f'Inspect the sample pump every {interval} days.',
                                      'The interval is measured from the most recent completed inspection.']),
        (3, '3 Exceptions', ['Stop the fictional pump if an inspection identifies a fault.',
                             'This exception does not change the scheduled inspection interval.']),
    ]:
        pdf.bookmarkPage(str(number))
        pdf.addOutlineEntry(title, str(number), level=0)
        pdf.setFont('Helvetica-Bold', 20)
        pdf.drawString(50, 730, title)
        pdf.setFont('Helvetica', 11)
        for offset, line in enumerate(lines):
            pdf.drawString(50, 685 - offset * 22, line)
        pdf.drawString(50, 40, f'Synthetic evidence only | Page {number}')
        pdf.showPage()
    pdf.save()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--python', required=True)
    args = parser.parse_args()
    if not shutil.which('pdftoppm'):
        parser.error('pdftoppm is required to render source pages for the review report; install Poppler separately')
    root = args.output.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=False)
    shutil.copytree(Path(__file__).resolve().parents[1] / 'template', root / 'vault')
    vault = root / 'vault'
    pdf = vault / '20_sources/synthetic-inspection.pdf'
    synthetic_pdf(pdf)
    source_hash = hashlib.sha256(pdf.read_bytes()).hexdigest()
    with contextlib.redirect_stdout(io.StringIO()) as sync_output:
        assert office.main(['--json'], default_root=vault) == 0, sync_output.getvalue()
    manifest = json.loads((vault / '_meta/source-manifest.json').read_text())
    source_id = next(record['source_id'] for record in manifest['records']
                     if record['current_source_path'] == '20_sources/synthetic-inspection.pdf')
    refresh(vault)
    readiness = doctor(python=args.python)
    assert readiness['ready'], readiness
    result = index_document(vault, source_id, python=args.python)
    indexed = load_index(vault, source_id)
    assert result['page_count'] == 3
    assert 'every 30 days' in indexed['pages'][1]['markdown']
    assert result['usage']['requests'] == 0
    assert hashlib.sha256(pdf.read_bytes()).hexdigest() == source_hash
    assert index_document(vault, source_id, python=args.python)['unchanged']
    context = build_document_context(vault, source_id, [2], task='What is the fictional inspection interval?', mode='frozen')
    assert context['document']['items'][0]['page'] == 2
    assert catalog.main(['--html', '--include-content'], root=vault) == 0
    shutil.copy2(vault / 'CATALOG.html', vault / 'CATALOG-before.html')
    shutil.copy2(pdf, root / 'source-before.pdf')
    frozen_path = vault / context['output_path']
    frozen_bytes = frozen_path.read_bytes()
    # Only our generated synthetic fixture changes, never an external source.
    synthetic_pdf(pdf, interval=14)
    assert ContextStore(vault).status(context['context_id'])['packs'][0]['freshness_state'] == 'stale'
    assert status_report(vault)['items'][0]['freshness_state'] == 'attention'
    assert catalog.main(['--html', '--include-content'], root=vault) == 0
    shutil.copy2(vault / 'CATALOG.html', vault / 'CATALOG-stale.html')
    with contextlib.redirect_stdout(io.StringIO()) as sync_output:
        assert office.main(['--json'], default_root=vault) == 0, sync_output.getvalue()
    refresh(vault)
    after = index_document(vault, source_id, python=args.python)
    assert after['source_hash'] != source_hash
    after_context = build_document_context(vault, source_id, [2], task='What is the fictional inspection interval?', mode='frozen')
    assert after_context['context_id'] != context['context_id']
    assert 'every 14 days' in after_context['document']['items'][0]['excerpt']
    assert frozen_path.read_bytes() == frozen_bytes
    assert catalog.main(['--html', '--include-content'], root=vault) == 0
    shutil.copy2(vault / 'CATALOG.html', vault / 'CATALOG-after.html')
    shutil.copy2(pdf, root / 'source-after.pdf')
    for name in ('source-before', 'source-after'):
        subprocess.run(['pdftoppm', '-png', '-r', '110', str(root / (name + '.pdf')),
                        str(root / (name + '-page'))], check=True, capture_output=True, timeout=30)
    report = {'doctor': readiness, 'index': result, 'status': status_report(vault),
              'context_id': context['context_id'], 'context_path': context['output_path'],
              'after_index': after, 'after_context_id': after_context['context_id'],
              'old_frozen_unchanged': frozen_path.read_bytes() == frozen_bytes,
              'vault': str(vault), 'scope': 'Actual SDK, ordinary Office sync, synthetic PDF, model-free only'}
    (root / 'proof.json').write_text(json.dumps(report, indent=2))
    before_text = context['document']['items'][0]['excerpt']
    after_text = after_context['document']['items'][0]['excerpt']
    review = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MirrorArc PDF change review</title><style>body{{font:17px/1.6 system-ui;max-width:1000px;margin:40px auto;padding:0 20px;background:#f6f9fb;color:#183647}}h1,h2{{line-height:1.2}}.note,section{{padding:24px;background:white;border:1px solid #d6e4e8;border-radius:12px;margin:20px 0}}.note{{border-left:5px solid #008f83}}.pair{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}a{{color:#006f68}}img{{display:block;width:100%;height:auto}}summary{{cursor:pointer}}@media(max-width:650px){{.pair{{display:block}}}}</style>
<h1>Can you verify what changed?</h1><p>Question: What is the fictional pump inspection interval?</p>
<div class="note"><strong>Scope of this demonstration</strong><br>PageIndex {html.escape(readiness['version'])} with pypdf {html.escape(readiness['dependencies']['pypdf'])} processed a synthetic PDF locally without a model. The labels below are authored expected interpretations, not AI-generated answers. This proves page evidence and change handling, not model quality or operational safety.</div>
<div class="pair"><section><h2>Before</h2><p>Expected interpretation: inspect every <strong>30 days</strong>.</p><h3>Extracted evidence from page 2</h3><pre>{html.escape(before_text)}</pre><details><summary>View original source page 2</summary><a href="source-before-page-2.png"><img src="source-before-page-2.png" alt="Rendered original PDF page 2: inspect every 30 days."></a><p><a href="source-before-page-2.png">Open full-size original page image</a></p></details><p><a href="source-before.pdf" download>Download original PDF</a> to open in your PDF reader.</p></section>
<section><h2>After</h2><p>Expected interpretation: the edited document now says <strong>14 days</strong>.</p><h3>Extracted evidence from page 2</h3><pre>{html.escape(after_text)}</pre><details><summary>View changed source page 2</summary><a href="source-after-page-2.png"><img src="source-after-page-2.png" alt="Rendered changed PDF page 2: inspect every 14 days."></a><p><a href="source-after-page-2.png">Open full-size changed page image</a></p></details><p><a href="source-after.pdf" download>Download changed PDF</a> to open in your PDF reader.</p></section></div>
<section><h2>What MirrorArc checked</h2><ul><li>The source hash changed and the old index was refused as current.</li><li>The earlier frozen evidence remained byte-for-byte unchanged.</li><li>The refreshed pack has a different identity and cites physical page 2.</li><li>No model request or private-source transfer was made.</li></ul><p>The document edit is hypothetical. It does not establish a real business policy or deployed system change.</p></section>
<section><h2>Your 5 minute review</h2><ol><li>Expand both source-page previews. Is the stated interval actually on page 2? Open a full-size image if the text is small. These images are rendered from the saved PDFs, not generated illustrations.</li><li>Compare the two excerpts. Can you explain exactly why the interpretation changes?</li><li>Open the <a href="vault/CATALOG-stale.html">stale Catalog</a> and then the <a href="vault/CATALOG-after.html">refreshed Catalog</a>. Select the PDF, then Document metadata, then PDF page evidence.</li><li>Tell us what remains confusing, whether the second interpretation is easier to verify, and roughly how long verification took.</li></ol><p>You are not being asked to accept the enterprise release. A real-model answer comparison and remaining release gates are still open.</p></section>
<details><summary>Technical evidence</summary><p>Before source SHA-256: <code>{source_hash}</code></p><p>After source SHA-256: <code>{after['source_hash']}</code></p><p><a href="proof.json">Machine-readable local proof</a></p></details></html>'''
    (root / 'REVIEW.html').write_text(review)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
