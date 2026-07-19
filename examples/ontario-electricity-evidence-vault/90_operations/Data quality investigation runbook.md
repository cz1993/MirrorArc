---
title: Data quality investigation runbook
type: runbook
status: active
domain: operations
created: 2026-07-19
updated: 2026-07-19
owner: MirrorArc Example
tags: [quality, investigation]
related: ["[[Quality gate pipeline]]", "[[Evidence workspace risk register]]"]
---

# Data quality investigation runbook

1. Stop dependent publication while preserving the failing source and derived evidence.
2. Identify the contract and exact failing row or field.
3. Compare the source note, prior version, and authoritative metadata.
4. Classify source defect, schema change, parser defect, or invalid assumption.
5. Fix code or contract without editing the authoritative source.
6. Rerun all affected gates and document the review decision.
