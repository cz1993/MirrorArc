---
title: Evidence workspace risk register
type: risk
status: monitored
domain: governance
created: 2026-07-19
updated: 2026-07-19
owner: MirrorArc Example
tags: [risk, governance]
related: ["[[Evidence controls]]", "[[Source freshness policy]]", "[[Forecast publication gate]]"]
---

# Evidence workspace risk register

| Risk | Trigger | Control |
| --- | --- | --- |
| Source license drift | Terms or dataset metadata changes | Recheck provenance before refresh |
| Stale source interpreted as current | Coverage year omitted | Visible snapshot labels and freshness checks |
| Forecast presented as operational | Synthetic output leaves evaluation context | Failing publication gate and prohibited-use text |
| Generated mirror edited manually | Mirror hash differs from manifest | Lifecycle conflict and sidecar migration |
| Reference-only body copied | IESO content appears in Git | No-data/provenance review and metadata-only rule |
