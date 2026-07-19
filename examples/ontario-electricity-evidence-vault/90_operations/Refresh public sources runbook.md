---
title: Refresh public sources runbook
type: runbook
status: active
domain: operations
created: 2026-07-19
updated: 2026-07-19
owner: MirrorArc Example
tags: [refresh, runbook]
related: ["[[Public data ingestion pipeline]]", "[[Source freshness policy]]", "[[Example release checklist]]"]
---

# Refresh public sources runbook

1. Resolve current catalogue metadata, resource URL, license, and modification timestamp.
2. Download to a disposable directory and compute SHA-256.
3. Compare file list, headers, notes, units, and coverage with the committed snapshot.
4. Update provenance and contracts before copying new files.
5. Run fixture tests, MirrorArc sync in a temporary copy, lint, no-data scan, and visual artifact checks.
6. Review every affected curated finding; do not carry conclusions forward automatically.
