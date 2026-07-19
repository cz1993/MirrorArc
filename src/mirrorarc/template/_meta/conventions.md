---
title: Conventions cheat sheet
type: note
status: active
domain: inbox
created: '2026-01-01'
updated: '2026-01-01'
owner: you
tags:
- meta
- conventions
related:
- '[[CLAUDE]]'
- '[[INDEX]]'
---

# Conventions Cheat Sheet

`_meta/agent-rules.md` and `_meta/profile.yml` are authoritative. This is the quick reference.

## Frontmatter

Required: `title`, `type`, `status`, `domain`, `created`, `updated`

Optional: `owner`, `tags`, `related`, `source`, `source_url`, `source_format`, `license`, `dataset`, `pipeline`, `model`, `decision`

## Domains

`inbox` - `context` - `sources` - `contracts` - `pipelines` - `analysis` - `models` - `outputs` - `governance` - `operations`

## Note Types

`hub` - `note` - `source-ref` - `source-mirror` - `dataset` - `data-contract` - `pipeline` - `model` - `evaluation` - `decision` - `risk` - `control` - `runbook` - `report` - `repo-mirror`

## Statuses

`draft` - `active` - `in-review` - `accepted` - `monitored` - `suppressed` - `superseded` - `archived`

## Generated Mirrors

- Office mirrors and optional PDF text mirrors live under `_mirrors/`.
- Repository mirrors live under `20_sources/repos/` by default.
- Edit originals, not generated mirror bodies.

## Working Disciplines

- Link generously.
- Consolidate before creating.
- Keep source-backed conclusions citeable.
