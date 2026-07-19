---
title: INDEX
type: hub
status: active
domain: inbox
created: '2026-01-01'
updated: '2026-01-01'
owner: you
tags:
- index
- moc
related:
- '[[CLAUDE]]'
- '[[INDEX]]'
---

# Data Product - Index

Welcome. This is the front door for people and AI agents working in this data-product workspace.
You do not need to understand the folder structure before you begin.

## First five minutes

1. **Name the outcome.** Add the product purpose, users, decisions, and success measures to a note
   in `10_context/`.
2. **Register evidence before interpreting it.** Add original files or source references under
   `20_sources/`; MirrorArc keeps those records authoritative.
3. **Generate the mirror layer.** Run `mirrorarc plan`, review the proposed actions, then run
   `mirrorarc sync` to create derived Markdown mirrors without modifying the originals.
4. **Open the portal.** Run `mirrorarc catalog --html --include-content`, then open `CATALOG.html`.
   Use Document view for content, Document metadata for trust and lifecycle details, and
   Relationship map for connected context.
5. **Build knowledge with restraint.** Update and link existing notes before creating new ones;
   cite the authoritative source and record important decisions or publication gates.

The workspace contract lives in `_meta/profile.yml`. Human and agent operating rules live in
[[_meta/agent-rules|agent rules]], and the one-screen reference lives in
[[_meta/conventions|conventions]].

## What MirrorArc protects

- Original files and repositories remain the source of truth.
- Generated mirrors are derived, refreshable, searchable, and agent-readable.
- Curated notes connect evidence, findings, decisions, and operating guidance.
- Provenance, lifecycle state, retention, and secrets-out rules stay visible.
- Consolidation is preferred over uncontrolled documentation growth.

## Starter Domains

| Domain | Folder | Purpose |
| --- | --- | --- |
| `inbox` | `00_inbox` | Triage lane for new sources, questions, and agent drafts. |
| `context` | `10_context` | Product purpose, stakeholder questions, scope, glossary, and system context. |
| `sources` | `20_sources` | Original source files, source references, repository fixtures, and provenance records. |
| `contracts` | `30_data-contracts` | Schemas, semantic definitions, quality expectations, and interface contracts. |
| `pipelines` | `40_pipelines` | Ingestion, transformation, orchestration, lineage, and validation workflows. |
| `analysis` | `50_analysis` | Exploratory work, evidence synthesis, findings, and reproducible analytical narratives. |
| `models` | `60_models` | Model definitions, evaluations, gates, limitations, and monitoring context. |
| `outputs` | `70_outputs` | Reports, briefings, dashboards, published datasets, and stakeholder-ready artifacts. |
| `governance` | `80_governance` | Licensing, privacy, security, retention, approvals, risks, controls, and decisions. |
| `operations` | `90_operations` | Runbooks, incidents, release records, support, freshness, and reliability evidence. |

## How this knowledge base works

- Source files and repositories remain authoritative.
- Generated mirrors make sources searchable and reviewable without replacing originals.
- Curated notes summarize, connect, and cite source-backed evidence.
- The profile contract defines domains, note types, statuses, templates, and generated views.

## Governance

[[_meta/agent-rules|agent rules]] - [[RETENTION]] (retention guidance) -
[[_meta/conventions|conventions]] - `log.md`
