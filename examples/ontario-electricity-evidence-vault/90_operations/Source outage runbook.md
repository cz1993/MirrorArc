---
title: Source outage runbook
type: runbook
status: active
domain: operations
created: 2026-07-19
updated: 2026-07-19
owner: MirrorArc Example
tags: [source, outage, runbook]
related: ["[[Source freshness policy]]", "[[Illustrative stale-source incident]]"]
---

# Source outage runbook

When a public URL is unavailable, retain the last verified version and mark its freshness state.
Do not substitute an unofficial mirror without provenance review. Record the failed URL, check
time, HTTP outcome, and affected consumers. Restore normal state only after the authoritative
resource and its terms are reverified.
