---
title: Demo walkthrough
type: runbook
status: active
domain: context
created: 2026-07-19
updated: 2026-07-19
owner: MirrorArc Example
tags: [demo, walkthrough]
related: ["[[INDEX]]", "[[Output relationship map]]"]
---

# Demo walkthrough

1. Open `CATALOG.html` and select an authored DOCX or XLSX source.
2. Follow the explicit arrow to its generated mirror under `_mirrors/`.
3. Inspect governed relationships, then render the `orientation` lens for a cited many-to-few view.
4. Toggle the document preview to compare the relationship map with rendered markdown.
5. Inspect [[Quality gate pipeline]] to see evidence-backed completeness and reconciliation rules.
6. Open the synthetic repo mirror to connect code, tests, configuration, and operational notes.

## Inspect a task before exporting

Choose a concrete question. Use `context build --lens orientation --mode metadata --query "source evidence" --json`
to inspect lexical selection, exact spans, freshness and exclusions. Save with `--mode dynamic`,
resolve the returned definition ID, then freeze the allowed evidence. In Catalog, open the selection
dialog to distinguish reference-only downloads from governed task commands and frozen status.
For code, keep the `--symbol demand_change` request when creating context; the Catalog command
preserves that selection. Local-tree hashes include working changes. Old frozen packs remain
unchanged and must be checked for staleness after a source mutation.
