---
title: Freshness dashboard specification
type: report
status: active
domain: operations
created: 2026-07-19
updated: 2026-07-19
owner: MirrorArc Example
tags: [freshness, dashboard]
related: ["[[Source freshness policy]]", "[[Illustrative stale-source incident]]"]
---

# Freshness dashboard specification

The view groups sources by committed snapshot, reference-only URL, L1 projection, and repo
fixture. It shows last checked, coverage period, source hash, projection lifecycle, license status,
and affected relationships, reviewed views, and frozen contexts. Red indicates a blocker; amber
indicates review; green indicates current evidence, never general truth.
