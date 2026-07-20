---
title: Annual demand contract
type: data-contract
status: accepted
domain: contracts
created: 2026-07-19
updated: 2026-07-19
owner: MirrorArc Example
dataset: ontario-energy-report-2023
tags: [demand, contract]
related: ["[[Ontario Energy Report 2023 supporting data]]", "[[2023 annual demand finding]]"]
---

# Annual demand contract

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| Year | integer | yes | Calendar year. |
| Total TWh | decimal | yes | Annual Ontario energy demand in terawatt-hours. |
| Change over Previous Year | decimal | yes | Source-reported year-over-year difference in TWh. |

Rows with blank years are ignored. Demand must be positive and years unique.
