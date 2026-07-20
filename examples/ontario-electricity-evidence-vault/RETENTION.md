---
title: RETENTION
type: note
status: active
domain: inbox
created: '2026-01-01'
updated: '2026-01-01'
owner: you
tags:
- governance
- retention
related:
- '[[CLAUDE]]'
- '[[INDEX]]'
---

# Retention Guidance

This starter is not legal, compliance, accounting, or records-management advice.
Replace these notes with profile-appropriate retention rules before production use.

## Defaults

| Category | Suggested handling |
| --- | --- |
| Source files | Keep originals in the authoritative source system. |
| Generated mirrors | Regenerate from source evidence when stale. |
| Curated notes | Archive when superseded or no longer useful. |
| Scratch work | Keep outside committed history and prune regularly. |

## Archival Process

1. Confirm the material is no longer active.
2. Move retained curated material under `_archive/` when appropriate.
3. Set frontmatter `status: archived` when the profile supports that state.
4. Do not delete source evidence without explicit human approval.

## Privacy And Sensitivity

- Keep private or regulated data outside this public scaffold.
- Never store secrets or credentials in the vault.
- Keep source-backed conclusions citeable to source paths or generated mirrors.
