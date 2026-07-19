---
title: Evidence lineage map
type: pipeline
status: active
domain: pipelines
created: 2026-07-19
updated: 2026-07-19
owner: MirrorArc Example
pipeline: evidence-lineage
tags: [lineage, relationships]
related: ["[[Artifact mirroring pipeline]]", "[[Evidence API contract]]", "[[Output relationship map]]"]
---

# Evidence lineage map

| Original | Generated mirror | Curated consumers |
| --- | --- | --- |
| `50_analysis/workbooks/historical-demand-profile.xlsx` | `_mirrors/50_analysis/workbooks/historical-demand-profile.md` | [[2023 annual demand finding]], [[Monthly demand range contract]] |
| `90_operations/briefs/data-quality-incident-review.docx` | `_mirrors/90_operations/briefs/data-quality-incident-review.md` | [[Data quality investigation runbook]], [[Illustrative stale-source incident]] |
| `_fixtures/repos/ontario-electricity-evidence-pipeline` | `20_sources/repos/ontario-electricity-evidence-pipeline.md` | [[Quality gate pipeline]], [[Data quality investigation runbook]] |

Generated paths appear after a local sync and remain intentionally absent from the committed source tree.
