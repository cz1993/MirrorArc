---
title: Public data ingestion pipeline
type: pipeline
status: active
domain: pipelines
created: 2026-07-19
updated: 2026-07-19
owner: MirrorArc Example
pipeline: public-data-ingestion
tags: [ingestion, open-data]
related: ["[[Ontario Energy Report 2023 supporting data]]", "[[Normalization pipeline]]", "[[Open data license register]]"]
---

# Public data ingestion pipeline

1. Resolve the Ontario Data Catalogue resource metadata and license.
2. Download the versioned ZIP to a disposable staging directory.
3. Verify the expected file list and record the ZIP SHA-256.
4. Copy only the documented fixture subset into `20_sources/open-data/`.
5. Run the no-data scan, contracts, and source-quality checks.

The committed snapshot is refreshed only through [[Refresh public sources runbook]].
