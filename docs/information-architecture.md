# Information Architecture

MirrorArc folders classify authoritative sources and operational controls; they do not require a
durable Markdown page for every concept. Cross-cutting meaning lives in profile metadata,
relationship ledger records, knowledge-view definitions, and context selections.

## Design principles

1. Keep L0 sources authoritative and L1 projections in the configured mirror boundary.
2. Give each opaque source identity at most one active projection identity.
3. Register readable Markdown/text directly unless policy requires a separate projection.
4. Express lineage and semantics as evidenced relationships rather than duplicate notes.
5. Render many sources through a few purpose-specific L2 views.
6. Keep reviewed output versioned and visibly stale after dependency change.
7. Keep publication, rights, sensitivity, retention, and promotion gates explicit.

## Allowed Markdown categories

| Category | Purpose | Persistence |
| --- | --- | --- |
| `index` | Manual scope, boundaries, and navigation guide (`INDEX.md`) | Manual exception |
| `authoritative_markdown_source` | Deliberately authored source record in a declared source/domain root | Authoritative |
| `l1_projection` | Machine-owned Markdown read model of an opaque source | Rebuildable |
| `l2_generated_view` | Generated purpose/audience view | Ephemeral or cache by default |
| `l2_reviewed_view` | Pinned/reviewed view version with provenance | Governed derived artifact |
| `operational_control` | Profile, policy, manifest, runbook, template, or runtime control | Explicitly classified |

Legacy curated derivatives and unknown Markdown remain readable migration inputs but are not target
categories.

## Default data-product domains

| Folder | Domain | What belongs here |
| --- | --- | --- |
| `00_inbox/` | `inbox` | Unadmitted sources, questions, and review work. |
| `10_context/` | `context` | Authoritative scope, stakeholder questions, and system context. |
| `20_sources/` | `sources` | Original files, registered readable sources, references, datasets, and repositories. |
| `30_data-contracts/` | `contracts` | Authoritative schemas, meanings, quality rules, and interfaces. |
| `40_pipelines/` | `pipelines` | Authoritative transformation, lineage, validation, and recovery definitions. |
| `50_analysis/` | `analysis` | Deliberately promoted analysis records; transient synthesis belongs in L2. |
| `60_models/` | `models` | Authoritative model definitions, evaluations, gates, and limitations. |
| `70_outputs/` | `outputs` | Deliberately published reports, decisions, and deliverables. |
| `80_governance/` | `governance` | Rights, privacy, retention, approvals, risks, and controls. |
| `90_operations/` | `operations` | Runbooks, incidents, releases, freshness, and recovery evidence. |

Generated Office/PDF projections live under `_mirrors/<canonical-source-path>.md`; repository
projections use the profile's `repo_notes_dir`. L2 files, when persistence is justified, live under
the configured governed-view boundary. `.mirrorarc/state.sqlite` contains rebuildable metadata,
not bodies or source authority.

The active map is `_meta/profile.yml`. `_meta/domain-map.yml` is a compatibility alias layer and
must not contradict it.

## Migration

Run `mirrorarc --root <vault> migration --json` before any cleanup. Review every Markdown category
and disposition. Planning never changes content. Write mode requires a reviewed worksheet and
backup, applies only approved moves/reclassification, preserves provenance, and leaves unrelated
files untouched.
