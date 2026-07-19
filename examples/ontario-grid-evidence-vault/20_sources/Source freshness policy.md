---
title: Source freshness policy
type: control
status: monitored
domain: sources
created: 2026-07-19
updated: 2026-07-19
owner: MirrorArc Example
tags: [freshness, source-control]
related: ["[[Refresh public sources runbook]]", "[[Freshness dashboard specification]]"]
---

# Source freshness policy

Committed source fixtures are versioned snapshots, not live feeds. Each source note records a URL,
license, version or coverage period, and last review date. A refresh must compare hashes, schema,
notes, license metadata, and derived conclusions before replacing the snapshot.

Reference-only sources are checked by URL and metadata. Their bodies remain outside the vault.
