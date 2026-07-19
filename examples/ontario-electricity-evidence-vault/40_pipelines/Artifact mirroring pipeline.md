---
title: Artifact mirroring pipeline
type: pipeline
status: active
domain: pipelines
created: 2026-07-19
updated: 2026-07-19
owner: MirrorArc Example
pipeline: mirrorarc-sync
tags: [mirrors, office, repos]
related: ["[[Evidence layers and trust]]", "[[Evidence lineage map]]", "[[Output relationship map]]"]
---

# Artifact mirroring pipeline

`mirrorarc plan` inventories supported Office/PDF sources and the configured local code fixture.
`mirrorarc sync` writes derived markdown under `_mirrors/` and `20_sources/repos/`, recording source
hashes and lifecycle state. Original binaries and code remain authoritative; curated notes remain
outside generated bodies.
