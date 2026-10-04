---
title: Workspace guide
type: index
status: active
domain: context
created: '2026-01-01'
updated: '2026-07-21'
markdown_category: index
---

# Workspace guide

This file is the manual navigation exception. Keep it short: explain the workspace purpose,
authority boundary, current lenses, and where review work lives. Do not maintain factual summaries
here when they can be rendered from governed sources and relationships.

## Start here

1. Read `_meta/agent-rules.md` and `_meta/profile.yml`.
2. Run `mirrorarc doctor`, `mirrorarc plan`, and `mirrorarc migration` before the first write.
3. Choose a task with `mirrorarc context build --lens orientation --mode metadata --query "your task" --json`.
   Inspect selected evidence, source hashes, ranking reasons and exclusions.
4. Review relationship proposals and stale L2 views.
5. Save the query with `--mode dynamic`, resolve its definition ID, then freeze allowed evidence.
   Open the Catalog selection dialog for saved commands and frozen status. Browser downloads are
   metadata-only; content inclusion is explicit, bounded and sensitivity-aware.

## Authority

- Original records and deliberately authored source Markdown are authoritative.
- L1 projections, relationships, L2 views, and context are derived and rebuildable.
- Generated or reviewed output does not become authority until explicitly promoted.

## Navigation

- **Sources and L1:** use `mirrorarc status` and the catalog lineage view.
- **Relationships:** use `mirrorarc relationships status`.
- **Knowledge views:** use `mirrorarc view list`.
- **Context:** use `mirrorarc context status`.
- **Review/recovery:** use `mirrorarc review`, `mirrorarc migration`, and `mirrorarc recovery`.

## Workspace-specific purpose

Replace this section with a concise statement of scope, intended users, trust boundaries, and the
few configured knowledge lenses that matter.
