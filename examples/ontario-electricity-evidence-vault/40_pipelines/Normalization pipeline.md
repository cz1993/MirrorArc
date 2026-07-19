---
title: Normalization pipeline
type: pipeline
status: active
domain: pipelines
created: 2026-07-19
updated: 2026-07-19
owner: MirrorArc Example
pipeline: normalize-public-series
tags: [normalization, semantics]
related: ["[[Public data ingestion pipeline]]", "[[Annual demand contract]]", "[[Generation output contract]]"]
---

# Normalization pipeline

The clean-room code fixture removes thousands separators, distinguishes quantities from
percentages, ignores blank terminal rows, and preserves source units in typed records. It does not
overwrite committed CSVs. Normalized outputs are disposable and can be recreated from sources and
contracts.
