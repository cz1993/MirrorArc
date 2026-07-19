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
related: ["[[Normalization pipeline]]", "[[Generation output contract]]", "[[Data quality investigation runbook]]"]
---

# Quality gate pipeline

Historical-data gates assert required fields, positive values, valid peak/minimum ordering, expected
fuel categories, and agreement between component values and reported totals within a documented
rounding tolerance. Failures retain evidence and create a review task; they do not silently coerce
or publish results.
