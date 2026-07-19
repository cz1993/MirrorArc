---
title: Quality gate pipeline
type: pipeline
status: monitored
domain: pipelines
created: 2026-07-19
updated: 2026-07-19
owner: MirrorArc Example
pipeline: quality-gates
tags: [quality, gates]
related: ["[[Normalization pipeline]]", "[[Illustrative model evaluation]]", "[[Forecast publication gate]]"]
---

# Quality gate pipeline

Structural gates assert required fields, positive values, valid peak/minimum ordering, and expected
fuel categories. A separate illustrative model gate suppresses publication when MAPE exceeds 5%.
Failures retain evidence and create a review task; they do not silently coerce or publish results.
