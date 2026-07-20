---
title: Evidence API contract
type: data-contract
status: accepted
domain: contracts
created: 2026-07-19
updated: 2026-07-19
owner: MirrorArc Example
tags: [api, contract, synthetic]
related: ["[[Artifact mirroring pipeline]]", "[[Evidence controls]]"]
---

# Evidence API contract

This synthetic interface models an agent-facing response, not a live service. Every item includes
`id`, `title`, `type`, `status`, `source_paths`, `related_ids`, and `updated`. A published answer
must include at least one resolvable source path and must label synthetic or reference-only inputs.
