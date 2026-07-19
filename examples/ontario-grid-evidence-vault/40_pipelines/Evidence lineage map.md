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
| `20_sources/briefs/ontario-grid-source-assessment.docx` | `_mirrors/20_sources/briefs/ontario-grid-source-assessment.md` | [[Public source register]], [[Open data license register]] |
| `50_analysis/workbooks/ontario-grid-evidence-scorecard.xlsx` | `_mirrors/50_analysis/workbooks/ontario-grid-evidence-scorecard.md` | [[Cross-source evidence synthesis]], [[Evidence controls]] |
| `70_outputs/briefings/ontario-grid-evidence-briefing.pptx` | `_mirrors/70_outputs/briefings/ontario-grid-evidence-briefing.md` | [[Stakeholder brief index]] |
| `_fixtures/repos/ontario-grid-evidence-pipeline` | `20_sources/repos/ontario-grid-evidence-pipeline.md` | [[Quality gate pipeline]], [[Forecast publication gate]] |

Generated paths appear after a local sync and remain intentionally absent from the committed source tree.
