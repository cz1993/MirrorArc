# MirrorArc Knowledge-Projection Implementation Plan

**Status:** implemented and locally verified through Workstream 10; not released or published

**Date:** 2026-07-21

**Architecture source:** [`MIRRORARC_WHITEPAPER.md`](MIRRORARC_WHITEPAPER.md)

**Execution prompt:** [`prompts/KNOWLEDGE_PROJECTION_KICKOFF.md`](prompts/KNOWLEDGE_PROJECTION_KICKOFF.md)

**Repository:** `/Users/cz/workspaces/cz1993/MirrorArc`

**Local proof completed:** 2026-07-21. The repository gate, fresh-install smoke test, deterministic
rebuild comparison, 280-source mixed-format Ontario lifecycle exercise, and automated plus human
portal validation passed locally. Commit, push, hosted CI, independent review, deployment, and
publication remain separate operator-gated delivery steps.

## 1. Objective

Implement MirrorArc as a governed knowledge-projection system that:

- preserves authoritative sources;
- gives each opaque source one stable L1 Markdown projection;
- stores typed, evidence-backed relationships as data rather than Markdown notes;
- generates many-to-few L2 knowledge views that are ephemeral unless pinned or reviewed;
- invalidates only affected relationships, views, reviews, and context when a source changes;
- assembles dynamic and frozen context packs;
- exposes the complete model in the portal;
- proves the result against an expanded, mixed-format Ontario electricity corpus.

The goal is not complete when the code compiles or unit tests pass. It is complete only after the
post-implementation Ontario corpus and portal validation in Workstream 10 passes.

## 2. Binding Principles

1. **L0 is authoritative.** Original files, repositories, exports, and intentionally authored
   records are never silently replaced by a mirror or model output.
2. **L1 is one source identity to one projection identity.** A clean projection can still be lossy;
   conversion warnings remain visible.
3. **Native readable sources are not duplicated without a reason.** Markdown and plain text may be
   registered directly as readable source records.
4. **Relationships are ledger records, not notes.** Every semantic relation carries evidence,
   method, hashes, freshness, and review state.
5. **L2 is many-to-few.** It must not become a second one-file-per-source mirror.
6. **Derived output is ephemeral by default.** Persistence requires a pin, review, audit, or
   reproducibility reason.
7. **Reviewed output is never silently overwritten.** Source changes mark it stale and may create a
   replacement candidate.
8. **`INDEX.md` is the manual guide exception.** It carries scope and navigation, not an
   unmaintainable factual summary.
9. **The deterministic core works without a model.** AI may propose semantics and views but cannot
   own source truth or lifecycle correctness.
10. **No vector database.** SQLite, explicit graph tables, and bounded text search are sufficient
    until evidence proves otherwise.
11. **No-data and rights gates remain release blockers.** Public examples contain only synthetic or
    permissively licensed material with provenance.

## 3. Current Baseline

The repository already has:

- package-owned Office/PDF and repository mirror engines;
- source and repository manifests, hashes, lifecycle states, audits, and recovery behavior;
- journaled changed-file capture, replay, reconciliation, locking, and full-sync recovery;
- profile contracts and packaged template copies;
- catalog and self-contained HTML portal generation;
- lint, no-data, conversion review, human review, benchmark, pilot, and release checks;
- the Ontario electricity example and public-safe provenance register.

The repository does not yet have:

- a first-class semantic relationship/provenance store;
- a dependency graph shared by journal, views, reviews, context, and portal;
- L2 lens definitions or generated/reviewed/stale view lifecycle;
- execution-grade dynamic and frozen context packs;
- portal support for evidenced semantic relationships and L2 views;
- linter rules that reject unexplained user-facing Markdown;
- a migration from the existing curated-note model;
- complex mixed-format end-to-end proof of the new architecture.

## 4. Scope and Non-Goals

### In scope

- canonical contract convergence;
- migration reporting and safe compatibility handling;
- L1 identity/cardinality enforcement;
- relationship and provenance ledger;
- dependency invalidation;
- L2 knowledge-view definitions, rendering, review, pinning, and staleness;
- context assembly;
- portal/catalog integration;
- template/profile/example migration;
- tests, documentation, and Ontario corpus validation.

### Out of scope unless required by an acceptance criterion

- embeddings or vector databases;
- hosted services or SaaS;
- broad connector development;
- package-part DOCX/PPTX/XLSX/PDF incrementality;
- an Obsidian plugin;
- a desktop shell;
- autonomous promotion of model output into authority;
- public deployment;
- importing private, proprietary, personal, client, or company data;
- private Ontario Grid analytics, forecasts, alerts, or client deliverables.

## 5. Technical Shape

The exact module split may change during implementation, but the intended ownership is:

```text
src/mirrorarc/
  relationships/
    model.py          # relationship types, evidence, state, validation
    store.py          # SQLite schema/migrations and repository API
    deterministic.py  # MIRRORS, domain, lifecycle, dependency edges
    proposals.py      # optional semantic proposal admission and review
    invalidation.py   # affected-subgraph calculation
  knowledge_views/
    definitions.py    # profile-owned lens contract
    render.py         # bounded source-backed view generation
    lifecycle.py      # generated/reviewed/stale/superseded transitions
    store.py          # definitions, outputs, versions, dependency hashes
  context.py          # dynamic definitions and frozen evidence packs
```

Shared derived state should remain in `.mirrorarc/state.sqlite` behind versioned migrations. Do
not create a second watcher, lifecycle authority, or unrelated database. Large bodies stay in
source/L1/L2 artifacts; the database stores metadata, bounded evidence anchors, hashes, and state.

Preferred CLI convergence:

```text
mirrorarc relationships refresh|status|review
mirrorarc view list|render|pin|review
mirrorarc context build|freeze|status
mirrorarc catalog --html [--include-content]
```

Names may be adjusted for consistency with `src/mirrorarc/cli.py`, but new behavior should be
grouped instead of creating one top-level command per report.

## 6. Workstream 0 — Contract Convergence

### Goal

Remove the old curated-wiki assumptions from all controlling contracts before code begins relying
on new semantics.

### Required changes

- Update `docs/PRODUCT.md`:
  - replace curated hubs/entity pages with relationship ledger and L2 views;
  - distinguish selection manifests from executable context packs;
  - describe the portal as current foundation plus planned semantic capability.
- Rewrite `docs/methodology.md` around L0, L1, relationships, L2, and context.
- Update `docs/information-architecture.md` so folders classify sources and controls rather than
  require one note per conceptual object.
- Update `docs/PROFILE_SCHEMA.md` with relationship vocabulary, knowledge lenses, Markdown
  categories, persistence policy, context budgets, and review rules.
- Update `docs/SYNC_SPEC.md`, `docs/RECOVERY.md`, and `docs/SECURITY_MODEL.md` with dependency
  invalidation, view state, context sensitivity, and rebuild behavior.
- Update root/template `AGENTS.md`, `_meta/agent-rules.md`, `_meta/conventions.md`, and templates so
  agents no longer create MOCs, entity pages, or durable knowledge notes by default.
- Reduce or retire note templates that exist only to encourage derived Markdown proliferation.
- Update `CHANGELOG.md` and any README/quickstart statements that still overstate the semantic
  graph or context-pack implementation.
- Run `scripts/sync_template_copies.py --write` after canonical template changes.

### Exit criteria

- `rg -n -i 'create.*(MOC|entity page|curated note|knowledge note)'` finds no active instruction to
  generate those artifacts by default outside migration/history text.
- Every canonical document uses the same authority and state terminology.
- All Markdown links resolve and template-copy checks pass.

## 7. Workstream 1 — Inventory and Migration Contract

### Goal

Understand every existing Markdown category before enforcing the new policy, and provide a safe,
reviewable migration path.

### Required changes

- Extend the migration/reporting surface to classify each `.md` file as one of:
  - `index`;
  - `authoritative_markdown_source`;
  - `l1_projection`;
  - `l2_generated_view`;
  - `l2_reviewed_view`;
  - `operational_control`;
  - `legacy_curated_derivative`;
  - `unknown`.
- Classify by declared source roots, manifest ownership, generated sentinels, frontmatter, and
  profile policy—not filename guesses alone.
- Produce a machine-readable report and a human worksheet showing recommended disposition:
  register as source, regenerate, convert to lens definition, pin/review, archive, or remove.
- Never delete or rewrite user content during a planning run.
- Add a reviewed write mode only after tests prove idempotence and recoverability.
- Preserve provenance when a reviewed L2 view is promoted to an authoritative Markdown source.

### Exit criteria

- The root template, packaged template, every built-in profile fixture, and Ontario example produce
  a complete classification with no unexplained Markdown.
- Re-running the migration report is deterministic.
- Write-mode tests prove that a backup/review gate is required and that unrelated files are not
  changed.

## 8. Workstream 2 — L1 Identity and Anti-Proliferation Invariants

### Goal

Make the one-source/one-projection rule and allowed Markdown categories enforceable.

### Required changes

- Add stable projection identity to the manifest if current mirror path alone is insufficient.
- Enforce at most one active L1 projection for each opaque source identity.
- Detect sibling mirrors, orphan mirrors, manual generated-body edits, and mirror/source hash drift.
- Register native Markdown/text sources as readable source records without mandatory duplication.
- Add profile policy for cases where native source isolation or immutable projection is required.
- Extend lint to reject unexplained user-facing Markdown while excluding declared operational
  controls, source Markdown, `INDEX.md`, L1, and governed L2 artifacts.
- Add explicit count/inventory output so operators can see:
  - authoritative source records;
  - opaque sources requiring L1;
  - active L1 projections;
  - L2 generated/reviewed/stale views;
  - unexplained Markdown.

### Exit criteria

- Every opaque active source has exactly one current L1 or a declared conversion failure.
- Native Markdown sources do not acquire redundant siblings by default.
- A second sync is idempotent and creates no new Markdown.
- Adding an unclassified generated note fails lint.
- Existing source preservation, annotation, move/delete, recovery, and journal tests remain green.

## 9. Workstream 3 — Relationship and Provenance Ledger

### Goal

Provide one shared, rebuildable source of derived relationship state.

### Required changes

- Add versioned SQLite tables for:
  - entities/artifact identities;
  - relationships;
  - evidence anchors;
  - relationship reviews;
  - dependency edges;
  - invalidation records;
  - schema metadata.
- Implement deterministic relationships first: `MIRRORS`, `DERIVED_FROM`, `IN_DOMAIN`, lifecycle,
  profile membership, review dependency, and context membership.
- Add typed semantic relationships: `MENTIONS`, `SAME_ENTITY`, `SUPPORTS`, `CONTRADICTS`,
  `SUPERSEDES`, `DEPENDS_ON`, and `GOVERNS`.
- Store source/mirror hashes, bounded evidence anchor, generation method/version, optional
  model/prompt version, confidence, state, timestamps, and invalidation reason.
- Treat model-derived relations as proposals until policy or review admits them.
- Make rebuild deterministic when only deterministic rules are enabled.
- Expose structured JSON status and export without copying full source bodies.

### Exit criteria

- The same source/manifests produce the same deterministic graph after deletion and rebuild.
- No relationship can be displayed as accepted without a deterministic rule or evidence/review
  record.
- Rejected and invalidated relationships remain auditable but are excluded from current views.
- Database migrations work from an existing technical-alpha journal database.
- No second event watcher or authority path is introduced.

## 10. Workstream 4 — Dependency Invalidation

### Goal

Make source changes propagate accurately and only as far as necessary.

### Required changes

- Connect successful journal application to the relationship dependency graph.
- On source create/change/move/delete:
  - update L1 and deterministic relations;
  - invalidate semantic relations tied to old hashes;
  - mark dependent reviewed views stale;
  - queue eligible generated views for replacement;
  - mark frozen context freshness appropriately;
  - keep dynamic context definitions intact so they resolve current state next time.
- Record the journal sequence and source hash that caused each invalidation.
- Add bounded affected-subgraph traversal and cycle protection.
- Keep full reconciliation able to repair missed invalidations.

### Exit criteria

- Changing one source does not scan, hash, reinterpret, or rewrite unrelated source bodies or
  views.
- A reviewed view is preserved and marked stale rather than overwritten.
- Move-only changes preserve semantic identity where evidence still resolves.
- Missed events followed by reconciliation produce the same final state as live capture.

## 11. Workstream 5 — L2 Knowledge Views

### Goal

Implement many-to-few human interpretation without returning to a curated-note factory.

### Required changes

- Add profile-owned lens definitions with:
  - purpose and audience;
  - source/relationship query;
  - required relationship/review state;
  - output structure;
  - citation rules;
  - content/token budget;
  - refresh and persistence policy.
- Implement deterministic lens rendering where possible before model synthesis.
- Add bounded model-assisted rendering behind an interface that records model and prompt versions.
- Implement states `generated`, `reviewed`, `stale`, `superseded`, and `failed`.
- Store view definition, dependency hashes, citations, generation record, and output hash.
- Default to cache/on-demand rendering; create a durable file only for pin, review, audit, or
  reproducibility.
- Add promotion workflow from reviewed view to new authoritative source, requiring explicit human
  intent and preserving derivation history.
- Prevent one-lens-per-source defaults in built-in profiles.

### Exit criteria

- One view can synthesize many sources and cite each factual section.
- Re-rendering unchanged dependencies is idempotent.
- Reviewed, stale, and generated candidates are visibly distinct.
- A profile cannot silently enable automatic promotion into authority.
- Tests demonstrate fewer persistent L2 artifacts than input sources for representative workflows.

## 12. Workstream 6 — Context Assembly

### Goal

Turn selection manifests into useful, governed task context.

### Required changes

- Preserve metadata-only export as a safe selection-manifest mode.
- Add dynamic context definitions that store purpose, selection rules, budgets, freshness policy,
  and permitted artifact types.
- Add frozen evidence packs containing bounded excerpts or resolvable content, citations, source
  and mirror hashes, relationship evidence, view versions, timestamps, sensitivity, and warnings.
- Enforce content/token/file-count budgets.
- Record omitted items and reasons rather than silently truncating.
- Make context construction deterministic when inputs and ordering are unchanged.
- Treat document content as untrusted evidence and prevent prompt instructions from changing
  selection or policy.

### Exit criteria

- A dynamic pack resolves newly current evidence after a source change.
- A frozen pack remains byte-stable and reports that newer source versions exist.
- A receiving agent can execute a defined offline task from a frozen pack without needing
  undocumented external context.
- Metadata-only mode never copies source, mirror, or view bodies.
- Content-inclusive modes inherit and display the vault's sensitivity and redistribution policy.

## 13. Workstream 7 — Portal and Catalog Integration

### Goal

Expose the new architecture without duplicating relationship or lifecycle logic in JavaScript.

### Required changes

- Extend the shared catalog report model to include governed relationship, evidence, view, and
  context state.
- Keep the safe catalog metadata-only by default.
- Collapse source/L1 pairs into one evidence card by default, with lineage expansion.
- Add filters for relationship type, evidence state, confidence, lifecycle, view state, source
  format, and freshness.
- Show evidence anchors and why a relationship exists.
- Add knowledge-view navigation and generated/reviewed/stale labels.
- Add dynamic/frozen context builder modes and budget feedback.
- Use clustering and progressive disclosure to avoid graph hairballs.
- Retain keyboard navigation, responsive layout, safe Markdown rendering, and no-network portable
  behavior.
- Do not add an independent portal database or relationship inference code.

### Exit criteria

- Every displayed semantic edge resolves to a ledger record and evidence state.
- Source authority and generated/reviewed/stale status are distinguishable without opening raw
  metadata.
- The portal remains usable with hundreds of sources and thousands of relationships.
- Metadata-only output contains no source or mirror bodies.
- Content-inclusive output is visibly labeled local/sensitive.
- Automated browser checks cover the critical navigation and context-building paths.

## 14. Workstream 8 — Templates, Profiles, and Ontario Migration

### Goal

Make new vaults start correctly and migrate the existing Ontario example without hiding the legacy
problem.

### Required changes

- Update built-in profiles to declare source roots, allowed Markdown categories, relationship
  vocabulary, lenses, persistence rules, and context budgets.
- Replace proliferation-oriented note templates with source-record, lens-definition, review, and
  promotion workflows.
- Keep `INDEX.md` short and manually understandable.
- Run the migration inventory against the existing Ontario vault.
- Convert valuable reusable structures into lens definitions or deterministic relations.
- Remove or archive legacy curated derivatives only after their disposition is reviewed and the
  new product can regenerate the intended knowledge from sources.
- Do not invent missing originals to justify legacy Markdown.
- Preserve the existing Ontario directory as the one flagship topic; do not create a parallel
  competing Ontario example.
- Update `examples/DATA_PROVENANCE.md`, `examples/README.md`, screenshots, and portal assets only
  after the migrated output is correct.

### Exit criteria

- A fresh `mirrorarc init` creates no default user-facing knowledge-note pile.
- Every Ontario Markdown file has an allowed category and provenance/state.
- The Ontario baseline contains source records, L1, operational controls, `INDEX.md`, and only
  deliberately generated/pinned/reviewed L2 views.
- Removing all derived state and rebuilding produces the same current L1, deterministic graph, and
  deterministic views.

## 15. Workstream 9 — Full Validation and Release Readiness

### Required automated gates

Run the narrowest relevant tests during development, then the complete local gate before any push:

```bash
python3.11 -m pytest
mirrorarc --root examples/ontario-electricity-evidence-vault lint
python3.11 scripts/sync_template_copies.py --check
python3.11 scripts/no_data_scan.py
python3.11 -m build
python3.11 -m pip check
git diff --check
```

Run these commands from an isolated Python 3.11 environment with the package and build tooling
installed. Adjust an invocation only if the package's canonical command surface changes, and do not
substitute a template-only check for the full suite.

### Required test matrix

- schema migrations from the current journal database;
- unit tests for identities, relations, evidence anchors, invalidation, view state, and context;
- property/idempotence tests for replay, rebuild, and unchanged regeneration;
- migration tests for every built-in profile and the Ontario example;
- no-proliferation lint tests;
- deterministic rebuild tests;
- one-changed-source structural performance tests;
- prompt-injection and untrusted-content tests;
- path, symlink, secret, PII, rights, and public-export tests;
- browser tests for the portal;
- packaging and fresh-install smoke tests on a disposable vault.

### Exit criteria

- All local tests and repository gates pass.
- Documentation and CLI help match implemented behavior.
- No generated cache, source data, portal output, or test residue is accidentally tracked.
- The current working tree is reviewed for unrelated pre-existing changes before staging.
- Hosted CI is used as confirmation only after the local gate passes and shipping is authorized.

## 16. Workstream 10 — Post-Implementation Ontario Corpus and Portal Proof

This is a post-code validation phase but part of the overall goal's finish line. Do not mark the
goal complete before it passes.

### 16.1 Corpus boundary

Continue using `examples/ontario-electricity-evidence-vault/` as the canonical Ontario electricity
topic and profile. Do not create a second flagship example with the same subject.

Two corpus tiers are permitted:

1. **Committed public subset:** synthetic or genuinely public, permissively licensed files with
   exact provenance and licence records. This subset may support the public demo.
2. **Large local stress corpus:** an operator-controlled disposable copy of the same Ontario vault
   for public but non-redistributable, very large, or uncertain-rights material. It remains outside
   Git and public portal artifacts. Prefer metadata-only references when the content cannot be
   stored safely.

Official publication does not prove redistribution rights. Non-official material requires the same
licence and provenance review. Never import private GuildBuild/Data Lab material, unpublished IESO
work, personal information, client data, forecasts, alerts, credentials, or proprietary analysis.

### 16.2 Acquisition scope

Research current sources live after the implementation is complete. Build a diverse evidence set
covering, where rights permit:

- Ontario government energy policy, planning, legislation, open data, and methodology;
- IESO public market rules, planning outlooks, reliability material, historical reports, and data
  directories;
- OEB public decisions, rate/regulatory material, open-data resources, and consumer guidance;
- federal or interprovincial energy context relevant to Ontario;
- municipal, academic, standards, industry, NGO, and other non-official analysis;
- historical datasets, glossaries, maps, technical reports, workbooks, and public repositories.

Exercise at least these source classes:

```text
PDF
DOCX
XLSX
CSV/TSV
Markdown/plain text
HTML or metadata-only web reference
PPTX when a relevant rights-cleared source is available
Git repository or structured code/config fixture
```

Target a minimum of 200 eligible source records and enough diversity to include at least five
opaque/readable format classes, ten independent publishers or source series, multiple dates or
versions, duplicate/superseded records, cross-source agreement and disagreement, and at least one
large file. A 500–1,000 record local stress corpus is encouraged when acquisition rights, storage,
and runtime remain reasonable. The committed public subset may be smaller.

For each acquired item record:

- publisher and title;
- canonical URL;
- retrieval date;
- licence and attribution;
- redistribution disposition;
- original filename and format;
- SHA-256;
- topic/date/version;
- whether the item is committed, metadata-only, synthetic, or local-validation-only.

Update `examples/DATA_PROVENANCE.md` for committed material. Store a machine-readable acquisition
manifest alongside the local validation evidence without committing restricted bodies.

### 16.3 End-to-end simulation

Create a disposable working copy from the canonical Ontario vault when destructive lifecycle tests
or non-committable sources are involved. Then run the product as a user would:

1. clean install or build the package in an isolated Python 3.11 environment;
2. run `doctor` and source-boundary checks;
3. run `plan` and inspect proposed admission and L1 actions;
4. run a full baseline sync;
5. build deterministic relationships and eligible semantic proposals;
6. generate the configured L2 views;
7. build dynamic and frozen context packs;
8. run status, lint, conversion-quality, review, and safety reports;
9. regenerate the local content-inclusive portal;
10. run a second unchanged pass and prove idempotence;
11. change one source and prove bounded refresh/invalidation;
12. move, delete, and restore selected sources and prove reconciliation/recovery;
13. rebuild derived state from sources and compare current hashes and counts.

Capture machine-readable evidence for source counts, L1 cardinality, relationship counts by type and
state, L2 counts and dependency sizes, invalidation fan-out, context budgets, warnings/errors,
converter calls, files read/hashed, and elapsed time.

### 16.4 Portal validation

Serve the generated portal locally and validate it with automated browser checks plus human visual
inspection. Required scenarios:

- start at `INDEX.md` and reach evidence within three interactions;
- search and filter hundreds of source records;
- inspect a collapsed source/L1 pair and expand its lineage;
- follow a typed semantic relationship to its evidence anchor;
- distinguish deterministic, proposed, accepted, rejected, and invalidated edges;
- open generated, reviewed, and stale knowledge views;
- observe a source change propagate to edge/view/context freshness;
- create a dynamic context definition and a frozen evidence pack;
- confirm metadata-only mode contains no bodies;
- confirm content-inclusive mode carries a local/sensitive warning;
- validate keyboard navigation, responsive layout, readable long filenames, no clipped cards or
  relationship labels, and no graph hairball at scale;
- verify all links and downloaded packs resolve correctly.

Use screenshots only as supporting visual evidence. Portal correctness must be backed by report,
ledger, hash, and browser-test evidence.

Do not deploy or update GitHub Pages during this phase unless the operator separately authorizes a
public release after rights, no-data, local tests, independent review, and hosted CI are green.

### 16.5 Final acceptance criteria

The implementation goal is complete only when:

- the complex Ontario corpus passes source, licence, provenance, and no-data gates;
- opaque-source/L1 cardinality is correct with no sibling or orphan mirrors;
- unexplained user-facing Markdown count is zero;
- deterministic relationships rebuild identically;
- semantic relationships carry evidence and explicit state;
- persisted L2 views remain materially fewer than source records;
- reviewed-view staleness and replacement behavior is proven;
- dynamic and frozen context behavior is proven;
- changed-source work is bounded to the affected dependency graph;
- recovery produces a consistent final state;
- the portal scenarios pass at target scale;
- all local repository, packaging, template, lint, and safety gates pass;
- the final report distinguishes implemented proof, known limitations, and any work still gated.

## 17. Delivery Sequence and Stop Rules

Workstreams are ordered. A later workstream may begin only when the contracts it depends on are
stable and its predecessor's tests pass.

```text
0 contracts
  → 1 migration inventory
  → 2 L1 invariants
  → 3 relationship ledger
  → 4 invalidation
  → 5 L2 views
  → 6 context
  → 7 portal
  → 8 templates/Ontario migration
  → 9 full local gate
  → 10 expanded Ontario proof
```

Stop and report a binding blocker when:

- safe migration would require deleting or reclassifying user-owned content without a review gate;
- a required source lacks redistribution or local-use rights;
- a model/provider is required for a mandatory deterministic acceptance criterion;
- source or derived content would cross a private/public boundary;
- an unchanged failing gate repeats with no new hypothesis;
- completion would require deployment, outreach, commit, push, merge, or another external action not
  explicitly authorized.

Do not call the goal complete because documentation is updated, a schema exists, synthetic unit
tests pass, or the portal renders a small fixture. The Ontario end-to-end proof is the finish line.

## 18. Required Completion Report

The final execution report must include:

- files and modules changed;
- architecture and migration decisions made;
- automated test commands and exact results;
- corpus composition and rights disposition;
- source/L1/L2/relationship/context counts;
- changed-source performance and invalidation evidence;
- portal URL used locally and browser scenarios passed;
- screenshots or visual evidence paths when created;
- remaining known limitations;
- git status and explicit statement of whether anything was committed, pushed, deployed, or
  published.
