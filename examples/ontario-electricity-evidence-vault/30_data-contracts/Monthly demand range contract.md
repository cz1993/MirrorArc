---
title: Monthly demand range contract
type: data-contract
status: accepted
domain: contracts
created: 2026-07-19
updated: 2026-07-19
owner: MirrorArc Example
dataset: ontario-energy-report-2023
tags: [demand, peak, contract]
related: ["[[Ontario Energy Report 2023 supporting data]]", "[[2023 peak demand finding]]"]
---

# Monthly demand range contract

Each record has `Year`, `Month`, `Peak MW`, and `Minimum MW`. Comma-formatted values are parsed as
integers. A valid row has a recognized month, positive values, and `Peak MW > Minimum MW`.
The contract does not infer an interval duration beyond what the source notes establish.
