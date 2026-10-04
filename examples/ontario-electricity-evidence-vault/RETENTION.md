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
| Authoritative Markdown records | Retain and dispose under the source policy. |
| L2 generated views | Ephemeral/cache by default; remove when superseded or expired. |
| L2 reviewed views | Preserve reviewed versions; mark stale and retain per review policy. |
| Scratch work | Keep outside committed history and prune regularly. |

## Archival Process

1. Confirm the material is no longer active.
2. Move retained authoritative material under `_archive/` only under its source policy.
3. Set frontmatter `status: archived` when the profile supports that state.
4. Do not delete source evidence without explicit human approval.

## Privacy And Sensitivity

- Keep private or regulated data outside this public scaffold.
- Never store secrets or credentials in the vault.
- Keep source-backed conclusions citeable to source paths or generated mirrors.
