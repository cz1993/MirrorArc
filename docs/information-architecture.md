# Information Architecture

MirrorArc's default `data-product` profile organizes knowledge by its role in the evidence path,
not by department. The stable sequence makes it easy for a human or agent to distinguish original
evidence, transformation logic, interpretation, publication, governance, and operations.

## Design Principles

1. **Separate source from interpretation.** Original files stay authoritative; generated mirrors
   live under `_mirrors/`; curated notes connect and interpret both.
2. **Make lineage visible.** Datasets link to contracts, contracts to pipelines, pipelines to
   analyses or models, and outputs back to the evidence that supports them.
3. **Keep top-level domains stable.** Add useful subfolders, but do not create a new top-level
   domain for every team, initiative, source system, or stakeholder.
4. **Use metadata for cross-cutting views.** `domain`, `type`, `status`, links, and source fields
   let the same artifact appear in multiple views without duplication.
5. **Keep publication gates explicit.** A failed quality, model, privacy, or licensing gate belongs
   in the graph rather than being hidden from the final narrative.

## Default Data-Product Domains

| Folder | Domain | What belongs here |
| --- | --- | --- |
| `00_inbox/` | `inbox` | New sources, unanswered questions, and drafts awaiting classification. |
| `10_context/` | `context` | Purpose, scope, stakeholders, questions, glossary, and system context. |
| `20_sources/` | `sources` | Original files, source references, provenance records, and repository mirrors under `repos/`. |
| `30_data-contracts/` | `contracts` | Schemas, grain, semantic definitions, quality expectations, and interfaces. |
| `40_pipelines/` | `pipelines` | Ingestion, transformation, orchestration, lineage, validation, and recovery. |
| `50_analysis/` | `analysis` | Exploratory work, evidence synthesis, findings, and reproducible narratives. |
| `60_models/` | `models` | Model definitions, evaluations, gates, limitations, and monitoring context. |
| `70_outputs/` | `outputs` | Reports, briefings, dashboards, published datasets, and stakeholder artifacts. |
| `80_governance/` | `governance` | Licensing, privacy, security, retention, decisions, approvals, risks, and controls. |
| `90_operations/` | `operations` | Runbooks, incidents, releases, freshness, support, and reliability evidence. |

Generated Office and PDF mirrors live at `_mirrors/<canonical-source-path>.md`. They retain the
source domain in frontmatter, so views can group source and mirror records while the source folders
stay clean. Repository mirrors default to `20_sources/repos/`.

The authoritative map is `_meta/profile.yml`. `_meta/domain-map.yml` is a generated compatibility
view for filing and migration; it must not contradict the profile contract.

## Applying The Pattern

The default profile works across industries because the stages remain the same even when the
subject changes:

| Use case | Typical emphasis |
| --- | --- |
| Public policy or energy | Public-source register, dataset contracts, reproducible analysis, licence controls, evidence briefings. |
| Commerce or operations | Transaction sources, metric contracts, transformation pipelines, KPI analysis, operational runbooks. |
| Research | Literature/source references, extraction contracts, synthesis, evaluation, published report. |
| Software data product | Repository sources, interface contracts, build pipelines, evaluations, release evidence. |

Use the packaged `business-operations`, `research-learning`, `software-project`, or `blank` profile
when its vocabulary fits better. Profiles are separate contracts; do not mix their top-level
folders into one vault unless you deliberately author and validate a custom profile.

## Migration

Run `mirrorarc --root <vault> migration` before moving folders. The report is read-only and uses
the current profile as the canonical destination map. `migration --runbook` prints a reviewed,
manual move protocol; MirrorArc does not silently reorganize sources.
