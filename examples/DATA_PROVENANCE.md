# Ontario Grid Example Data Provenance

This register is the release boundary for MirrorArc's committed flagship example. The corpus uses
only public material with a documented reuse basis, independently authored files, or synthetic
fixtures. It contains no private GuildBuild project files, company data, personal data, secrets,
credentials, or live operating data.

Licence and source boundaries were reviewed on 2026-07-19.

## Public OGL Ontario Source Package

The files below were selected without modification from the Ontario Data Catalogue resource
"Ontario Energy Report — Supporting Data" for the 2023 report:

- Dataset: `https://data.ontario.ca/dataset/ontario-energy-report-supporting-data`
- Resource archive: `https://data.ontario.ca/dataset/331c8cae-858f-4d72-8f44-0d66e6aa6d24/resource/d92aee20-dfd5-46b5-a2e4-f0c1a932067c/download/opendata.zip`
- Downloaded archive SHA-256: `2df0e2aec3b4c11103ee2fe67dbdb4e7fb344f0d6228ccb378bcc036bb9e956a`
- Licence: Open Government Licence — Ontario, `https://www.ontario.ca/page/open-government-licence-ontario`
- Attribution: Contains information licensed under the Open Government Licence — Ontario.

| Committed path | Status |
| --- | --- |
| `examples/ontario-grid-evidence-vault/20_sources/open-data/ontario-energy-report-2023/exports-gwh.csv` | Included from the OGL Ontario archive. |
| `examples/ontario-grid-evidence-vault/20_sources/open-data/ontario-energy-report-2023/forecast-demand-peaks.csv` | Included from the OGL Ontario archive. |
| `examples/ontario-grid-evidence-vault/20_sources/open-data/ontario-energy-report-2023/generation-emissions-intensity.csv` | Included from the OGL Ontario archive. |
| `examples/ontario-grid-evidence-vault/20_sources/open-data/ontario-energy-report-2023/generation-output-by-fuel-type-grid-connected-gwh.csv` | Included from the OGL Ontario archive. |
| `examples/ontario-grid-evidence-vault/20_sources/open-data/ontario-energy-report-2023/generation-output-by-fuel-type-grid-connected-percent.csv` | Included from the OGL Ontario archive. |
| `examples/ontario-grid-evidence-vault/20_sources/open-data/ontario-energy-report-2023/greenhouse-gas-emissions-ontario-electricity.csv` | Included from the OGL Ontario archive. |
| `examples/ontario-grid-evidence-vault/20_sources/open-data/ontario-energy-report-2023/historical-annual-ontario-energy-demand-twh.csv` | Included from the OGL Ontario archive. |
| `examples/ontario-grid-evidence-vault/20_sources/open-data/ontario-energy-report-2023/historical-monthly-generation-output-by-fuel-type-mwh.csv` | Included from the OGL Ontario archive. |
| `examples/ontario-grid-evidence-vault/20_sources/open-data/ontario-energy-report-2023/historical-monthly-ontario-demand-peaks-minimums-mw.csv` | Included from the OGL Ontario archive. |
| `examples/ontario-grid-evidence-vault/20_sources/open-data/ontario-energy-report-2023/imports-gwh.csv` | Included from the OGL Ontario archive. |
| `examples/ontario-grid-evidence-vault/20_sources/open-data/ontario-energy-report-2023/ontario-demand-peaks-minimums-mw.csv` | Included from the OGL Ontario archive. |
| `examples/ontario-grid-evidence-vault/20_sources/open-data/ontario-energy-report-2023/ontario-peak-demand-mw.csv` | Included from the OGL Ontario archive. |

The adjacent `*-notes-en.txt` files are also selected unchanged from the same archive. The source
directory README preserves the dataset URL, resource URL, archive hash, and attribution.

## Reference-Only Public Pages

Independently authored source-reference notes link to the IESO Data Directory, Annual Planning
Outlook, Reliability Outlook, Year in Review, and generation/zonal reference pages. Only URLs,
titles, retrieval context, and MirrorArc-authored constraints are committed. No IESO page body,
table, chart, downloadable dataset, logo, or other asset is copied. Those notes use
`license: reference-only`.

The OEB open-data page is treated the same way unless a specific resource supplies a compatible
licence. A public URL is not, by itself, permission to redistribute its content.

## Independently Authored Office And PDF Artifacts

These files were created specifically for this repository. Facts drawn from the OGL source files
are cited or clearly scoped to the historical 2023 snapshot. All other narrative is independent
MirrorArc example content and is covered by this repository's licence.

| Committed path | Purpose |
| --- | --- |
| `examples/ontario-grid-evidence-vault/10_context/briefs/ontario-grid-project-charter.docx` | Data-product charter and stakeholder questions. |
| `examples/ontario-grid-evidence-vault/20_sources/briefs/ontario-grid-source-assessment.docx` | Source suitability and licensing assessment. |
| `examples/ontario-grid-evidence-vault/80_governance/briefs/public-corpus-governance-memo.docx` | Public-corpus boundary and controls. |
| `examples/ontario-grid-evidence-vault/90_operations/briefs/data-quality-incident-review.docx` | Fictional quality incident used to exercise operations documentation. |
| `examples/ontario-grid-evidence-vault/20_sources/workbooks/open-data-inventory.xlsx` | Source inventory and classification workbook. |
| `examples/ontario-grid-evidence-vault/50_analysis/workbooks/historical-demand-profile.xlsx` | Historical public-demand analysis workbook. |
| `examples/ontario-grid-evidence-vault/50_analysis/workbooks/ontario-grid-evidence-scorecard.xlsx` | Evidence and release-readiness scorecard. |
| `examples/ontario-grid-evidence-vault/60_models/workbooks/illustrative-model-evaluation.xlsx` | Synthetic model predictions and failed publication gate. |
| `examples/ontario-grid-evidence-vault/70_outputs/briefings/ontario-grid-evidence-briefing.pptx` | Source-to-decision stakeholder briefing. |
| `examples/ontario-grid-evidence-vault/70_outputs/briefings/evidence-governance-review.pptx` | Licensing and governance briefing. |
| `examples/ontario-grid-evidence-vault/70_outputs/reports/ontario-grid-evidence-methodology.pdf` | Two-page methodology report. |
| `examples/ontario-grid-evidence-vault/70_outputs/reports/ontario-grid-evidence-pack.pdf` | Two-page historical evidence pack. |

## Synthetic Repository And Model Fixtures

| Path | Status | Notes |
| --- | --- | --- |
| `examples/ontario-grid-evidence-vault/_fixtures/repos/ontario-grid-evidence-pipeline/` | Synthetic, independently authored fixture licensed under its included MIT License. | Exercises local repository mirroring, contracts, source loading, validation, and a publication gate. It contains no copied private project code. |
| `examples/ontario-grid-evidence-vault/tools/repos.yml` | MirrorArc example configuration. | Points only to the local synthetic fixture. |
| `examples/ontario-grid-evidence-vault/60_models/workbooks/illustrative-model-evaluation.xlsx` | Synthetic predictions. | The calculated 7.7% MAPE intentionally exceeds the 5% gate and remains suppressed. It is not a forecast of Ontario demand. |

## Generated Locally, Never Committed As Sources

Running `tools/mirrorarc.py sync` creates Markdown mirrors under `_mirrors/`, a repository mirror at
`20_sources/repos/ontario-grid-evidence-pipeline.md`, and manifest/audit state under `_meta/` and
`.mirrorarc/`. These are reproducible derivatives of the registered sources and remain ignored in
the source example.

Private users may connect actual project material under `_private-overlay/`. That directory is
ignored and is expressly outside this repository's provenance and tests.
