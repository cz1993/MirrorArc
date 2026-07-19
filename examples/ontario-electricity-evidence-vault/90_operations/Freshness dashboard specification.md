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

The view groups sources by committed snapshot, reference-only URL, generated mirror, and repo
fixture. It shows last checked, coverage period, source hash, mirror lifecycle, license status, and
affected curated notes. Red indicates a blocker; amber indicates review; green indicates current
evidence, never general truth.
