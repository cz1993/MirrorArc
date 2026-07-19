---
title: Forecast publication gate
type: decision
status: suppressed
domain: models
created: 2026-07-19
updated: 2026-07-19
owner: MirrorArc Example
model: seasonal-naive-demo
decision: suppress-publication
tags: [gate, synthetic]
related: ["[[Illustrative model evaluation]]", "[[Evidence controls]]", "[[Historical peak model card]]"]
---

# Forecast publication gate

- **Decision:** do not publish the illustrative model result.
- **Evidence:** synthetic evaluation MAPE is 7.7%; the defined threshold is at most 5.0%.
- **Consequence:** keep the model and evaluation visible for documentation and testing; expose no
  live forecast, alert, probability, or planning claim.
- **Review trigger:** a new independently validated evaluation and explicit operator approval.
