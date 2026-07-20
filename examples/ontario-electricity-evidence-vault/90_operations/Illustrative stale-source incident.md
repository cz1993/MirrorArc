---
title: Illustrative stale-source incident
type: risk
status: archived
domain: operations
created: 2026-07-19
updated: 2026-07-19
owner: MirrorArc Example
tags: [incident, synthetic]
related: ["[[Source outage runbook]]", "[[Freshness dashboard specification]]"]
---

# Illustrative stale-source incident

Synthetic scenario: a catalogue URL changed while a cached CSV remained readable. The workspace
kept the prior snapshot, marked the source stale, suppressed dependent refresh claims, and required
a metadata and license recheck. No live Ontario source outage is asserted.

Learning: reachability, freshness, and authorization are separate states and should be visible.
