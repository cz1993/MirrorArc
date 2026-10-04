---
title: Conventions cheat sheet
type: operational-control
status: active
domain: inbox
created: '2026-01-01'
updated: '2026-07-21'
markdown_category: operational_control
---

# Conventions Cheat Sheet

`_meta/agent-rules.md` and `_meta/profile.yml` are authoritative.

## Durable Markdown categories

`index` · `authoritative_markdown_source` · `l1_projection` · `l2_generated_view` ·
`l2_reviewed_view` · `operational_control`

## Identity and authority

- Originals remain authoritative.
- One active opaque source identity normally has one active L1 projection.
- Native Markdown/text may be registered directly.
- Relationships are evidenced ledger records, not notes.
- L2 is many sources to few views and ephemeral by default.
- Reviewed views become stale; they are not silently overwritten.

## Working discipline

- Plan and classify before writing.
- Cite stable source/projection identities and hashes.
- Keep model proposals separate from accepted relations.
- Choose metadata-only, dynamic, or frozen context deliberately.
- Promote a view to authority only through explicit human intent.
- Run lint and reconciliation after material changes.
