---
title: Evidence controls
type: control
status: monitored
domain: governance
created: 2026-07-19
updated: 2026-07-19
owner: MirrorArc Example
tags: [controls, quality]
related: ["[[Evidence workspace risk register]]", "[[Quality gate pipeline]]", "[[Artifact mirroring pipeline]]"]
---

# Evidence controls

- Exact external binary/CSV paths appear in `examples/DATA_PROVENANCE.md`.
- CI scans committed and generated mirror text for high-risk patterns.
- Contracts separate units, row types, quantities, percentages, and source versus derived fields.
- Mirror manifests preserve source hashes and generated-body integrity.
- Data-quality gates fail closed and remain linked to validation evidence.
- Reference-only sources never enter the conversion pipeline.
