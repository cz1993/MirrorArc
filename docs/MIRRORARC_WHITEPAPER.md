# MirrorArc Whitepaper

**Status:** canonical product architecture and implementation direction

**Date:** 2026-07-21

**Repository reviewed:** `cz1993/MirrorArc` at commit `0995caca7ad28bcb89c5ebc0fa7572b83621e8e1`

**Audience:** maintainers, design partners, knowledge-management teams, consulting operators, and technical reviewers

**Implementation state:** the local working tree implements source mirroring, journaled refresh,
relationships, knowledge views, and context assembly. The Trustworthy Context batch validates
integrity and opt-in task retrieval; planning-session acceptance and shipment remain pending.

## 1. Executive Summary

Creating documentation used to be expensive. Generative AI has made creation cheap, but it has
not made the resulting document collections easy to read, reconcile, trust, or maintain. In many
workspaces the new failure mode is not missing documentation. It is an excess of summaries,
entity pages, hubs, and agent-authored notes whose authority and freshness are unclear.

MirrorArc exists to preserve the information and knowledge in a source collection while
minimizing the number of durable documents that must be governed.

Its product thesis is:

> **Preserve authoritative records. Treat every durable derivative as a maintenance liability.
> Generate views instead of accumulating documents.**

MirrorArc should therefore become a **governed knowledge-projection system**, not an
AI-maintained wiki. It should:

1. preserve original documents and repositories as authoritative records;
2. create a stable, inspectable Markdown projection for each opaque source;
3. maintain evidence-backed relationships without requiring more Markdown notes;
4. generate a small number of human-readable knowledge views from many sources;
5. refresh only affected projections, relationships, views, and context as sources change;
6. expose provenance, lifecycle, review state, and staleness in the portal;
7. assemble bounded context for agents without making that context a new source of truth.

The concise product statement is:

> **MirrorArc turns changing source collections into governed, source-backed knowledge
> projections that people and AI agents can inspect, connect, cite, and refresh without replacing
> the original records or creating another pile of documentation.**

## 2. Architectural Decision

MirrorArc will use two distinct projection layers around an evidence-backed relationship ledger:

- **L1 — Specular projection:** a source-addressed, machine-owned Markdown representation designed
  for inspection, search, diffing, citation, and agent use;
- **Relationship and provenance ledger:** typed connections between sources, mirrors, claims,
  entities, lifecycle events, and derived outputs, with evidence and invalidation state;
- **L2 — Diffuse knowledge views:** audience- or task-specific reading views generated from many
  sources and relationships, ephemeral by default and persistent only through an explicit pin or
  review decision.

This replaces the earlier assumption that agents should routinely create MOCs, entity pages,
summaries, and knowledge notes as durable Markdown. Those artifacts created an internal
contradiction: anti-proliferation rules attempted to control a document factory that the
methodology itself encouraged.

The new rule is:

> **A relationship is data, not a document. A synthesis is a view, not a record, until a human
> deliberately promotes it into an authoritative record.**

## 3. What MirrorArc Governs

MirrorArc targets source-backed, lifecycle-sensitive collections where:

- original records or repositories exist;
- sources change over time;
- provenance and source authority matter;
- people or agents need to reconcile information across many artifacts;
- stale interpretation creates risk or repeated effort;
- a durable audit trail is more valuable than a transient chat answer.

Good fits include consulting and advisory workspaces, policy and due diligence, operational and
compliance collections, research and literature review, software documentation, and complex
learning collections.

MirrorArc is not:

- a generic personal note-taking system;
- an autonomous wiki author;
- a vector database product;
- a document-management-system replacement;
- a guarantee that Markdown reproduces every visual or semantic detail of an Office/PDF source;
- a system that turns model output into authority without review.

## 4. Core Principles

### 4.1 Authority before convenience

Original files, repositories, exports, and intentionally authored decisions remain authoritative.
Derived projections must always reveal what they came from and how current they are.

### 4.2 Minimize durable derivatives

Every persistent derivative has a creation cost, review cost, invalidation cost, retention cost,
and risk of being mistaken for authority. MirrorArc should create a file only when persistence is
required for reproducibility, review, interoperability, or an explicit user decision.

### 4.3 One source identity, one L1 projection identity

For an opaque source such as DOCX, PDF, PPTX, or XLSX, one active source identity normally maps to
one active Markdown mirror identity. Moves may change paths without changing identity. Repeated
syncs must not create siblings or alternate summaries.

This is an identity, cardinality, and lineage guarantee. It is not a claim of byte-for-byte,
layout-for-layout, or meaning-for-meaning equivalence. The source remains authoritative.

Already-readable Markdown and plain-text sources do not require a redundant copy merely to satisfy
a file-count rule. They may be registered as L1-readable source records unless isolation,
normalization, or immutable snapshotting requires a separate projection.

### 4.4 Relationships carry evidence

Semantic connections must be traceable to source or mirror spans, hashes, and generation methods.
An unexplained graph edge is a suggestion, not knowledge.

### 4.5 Many sources produce few human views

L2 is not a second one-document-per-source mirror. A knowledge view answers a purpose: orient a
new reader, compare positions, explain a process, trace a decision, summarize change, or prepare a
task. Its cardinality is many sources to few useful views.

### 4.6 Events trigger work; reconciliation establishes completeness

Filesystem and provider events are advisory. Durable journaling, stable-source checks, hashing,
idempotent replay, startup reconciliation, scheduled reconciliation, and full recovery sync remain
mandatory.

### 4.7 AI may interpret but cannot establish source truth

Models may propose relationships, explanations, and views. They do not own source identity,
hashes, mirror correctness, lifecycle truth, review status, or authoritative decisions.

## 5. Target Architecture

| Layer | Responsibility | Authority and persistence |
| --- | --- | --- |
| L0 authoritative sources | Original files, repositories, exports, and deliberately authored records | Authoritative; preserved according to source policy |
| Change journal | Observed changes, retries, sequencing, checkpoints, and recovery | Operational and rebuildable; never source truth |
| L1 specular projections | Machine-owned Markdown and extraction metadata | Derived, inspectable, and reproducible |
| Relationship and provenance ledger | Typed, evidenced links plus dependency and invalidation state | Derived core state; deterministic or proposal/review governed |
| L2 knowledge views | Human-readable, audience/task-specific synthesis | Derived and ephemeral by default; pin/review creates a governed artifact |
| Context assembly | Dynamic selections and frozen evidence packs | Derived execution input; never authority |
| Presentation | `INDEX.md`, catalog, portal, Obsidian, CLI, MCP, and exports | Interface over shared state; no independent truth |
| Profile control plane | Source scope, policies, relationship vocabulary, lens definitions, review gates, and views | Versioned contract |

The core flow is:

```text
authoritative sources
        ↓
change capture + reconciliation
        ↓
durable journal
        ↓
L1 specular projections + manifests + audit
        ↓
relationship/provenance ledger
        ↓
L2 knowledge views + context assembly
        ↓
INDEX / catalog / portal / Obsidian / MCP
```

All layers after L0 remain replaceable. A backup of only derived state is not a backup of the
knowledge collection.

## 6. L1 Specular Projection Contract

A MirrorArc L1 projection is a manifest-backed, deterministic, machine-owned read model of an
authoritative source. It exists to make opaque evidence inspectable without mutating the source.

The implementation contract is:

- stable source IDs and mirror IDs are manifest-owned, not path-owned;
- one active opaque source normally has exactly one active L1 mirror;
- source bytes, source hash, converter version, configuration version, mirror path, lifecycle
  state, warnings, and errors are recorded;
- generated mirrors are machine-owned and protected from durable inline editing;
- mirror writes are atomic and preserve the previous valid mirror on failure;
- unchanged sources do not produce content diffs or new files;
- source moves preserve identity when unambiguous;
- source deletion changes lifecycle state and does not silently erase evidence;
- full sync remains the recovery and verification path;
- changed-file sync remains the normal steady-state path.

Conversion quality must be explicit. A clean lifecycle state means that the declared converter ran
successfully against the recorded source hash. It does not mean that every table, image, formula,
scan, comment, or layout relationship was captured.

## 7. Relationship and Provenance Ledger

The relationship ledger is a minimal core capability, distinct from an optional full-text evidence
index. It may use SQLite and must remain rebuildable from sources, manifests, deterministic rules,
and accepted semantic records.

Initial relationship types should include:

```text
MIRRORS
DERIVED_FROM
IN_DOMAIN
MENTIONS
SAME_ENTITY
SUPPORTS
CONTRADICTS
SUPERSEDES
DEPENDS_ON
GOVERNS
INVALIDATES
IN_CONTEXT
```

Every relationship records at least:

```text
relationship_id
from_id
to_id
relationship_type
source_id and source_hash
mirror_id and mirror_hash when applicable
evidence anchor or deterministic rule
generation method and version
model and prompt version when applicable
confidence when applicable
review state
created_at
invalidated_at
```

Deterministic relationships such as `MIRRORS`, lifecycle, profile membership, and manifest
dependency may be accepted automatically. Model-derived semantic relationships begin as proposals.
They may be displayed with confidence and evidence, reviewed, rejected, or invalidated, but they
must not be presented as source facts merely because a model produced them.

Evidence anchors should be durable enough to re-resolve after regeneration. Store source/mirror
hashes plus bounded exact text and surrounding context where text anchoring is appropriate. Do not
copy entire source bodies into the ledger.

## 8. L2 Diffuse Knowledge Views

A knowledge view is a generated reading surface defined by:

- a purpose or question;
- an intended audience;
- source and relationship selection rules;
- a format or lens template;
- a content/token budget;
- citation and freshness requirements.

Examples include:

- an orientation brief for a new project member;
- a comparison of two policy positions;
- a timeline assembled from many records;
- a decision-support view showing evidence for and against an option;
- a change digest for sources modified since the last review;
- a process explanation with source-backed steps.

Knowledge views use explicit states:

```text
generated
reviewed
stale
superseded
failed
```

An unreviewed generated view may be replaced automatically. When a reviewed view's dependencies
change, the reviewed artifact becomes `stale`; MirrorArc may generate a replacement candidate but
must not overwrite the approved version silently.

Pinning a view persists its definition and governed output. If a person adopts a synthesis as a
policy, decision, report, or other record for which they accept authority, it leaves the derived
view layer and becomes a new L0 authoritative source with its own lifecycle.

The default persistence rule is:

> **Do not create a durable L2 file unless a user pins it, reviews it, or a reproducibility
> requirement explicitly calls for it.**

## 9. `INDEX.md` and Authored Markdown

`INDEX.md` is the intentional manual exception to the anti-proliferation default. It defines the
workspace's purpose, scope, operating boundaries, and navigation entry points. It should not become
a manually maintained factual summary of the collection.

Allowed durable Markdown categories are:

- `INDEX.md` as the human guide;
- authoritative Markdown sources stored in declared source roots;
- machine-owned L1 projections;
- pinned or reviewed L2 views with complete provenance and state;
- operational and governance files required by the MirrorArc runtime.

Untracked summaries, MOCs, entity pages, and agent-created knowledge notes are not a default
content category. A linter should require every user-facing Markdown file to declare which allowed
category it belongs to.

## 10. Journaled Incremental Refresh

The current journaled materialization foundation remains valid. The useful database analogy is a
materialized view or CQRS read model, not literal write-ahead-log shipping.

Normal source processing is:

```text
observe create/change/move/delete
    → coalesce and settle
    → validate source boundary
    → fingerprint and hash candidate
    → update L1 only when needed
    → invalidate affected relationships, views, reviews, and frozen-context freshness
    → recompute the affected subgraph and eligible generated views
    → expose lag, failures, and review work
```

The system provides at-least-once delivery with idempotent application. It does not claim exactly
once processing.

Required safeguards remain:

- Office lock-file suppression;
- file-stability checks before and after conversion;
- atomic mirror replacement;
- workspace locking;
- retryable and terminal failure states;
- startup and scheduled reconciliation;
- explicit full-sync recovery;
- path, symlink, source-boundary, and output-boundary validation.

Recomputation must be dependency-bounded. A change to one source should not reinterpret the entire
collection unless the changed relationship genuinely affects a collection-wide view.

## 11. Model Policy

### Tier 0 — deterministic core

No model is required for:

- source discovery and identity;
- event capture and replay;
- hashing and lifecycle state;
- L1 generation;
- deterministic relationships;
- dependency invalidation;
- reconciliation and recovery;
- audit records.

### Tier 1 — bounded semantic proposals

A lightweight model may receive changed chunks, bounded context, selected relationships, and
explicit profile vocabulary. It may propose:

- entities and typed relationships;
- evidence anchors;
- a semantic change explanation;
- affected generated or reviewed views;
- a bounded L2 view candidate.

Each proposal is tied to source and mirror hashes, model identity, prompt version, and review state.

### Tier 2 — explicit cross-document interpretation

A larger model may be invoked for deliberate multi-source synthesis or task-specific context
assembly. This is an explicit operation, not a hidden steady-state dependency.

Source and mirror content remain untrusted evidence. Document text cannot override MirrorArc
policy, request tool execution, or grant itself authority.

## 12. Context Assembly

MirrorArc needs two context-pack modes.

### Dynamic saved context

A dynamic context definition stores selection rules, purpose, budgets, required relationship
types, and freshness policy. It resolves the current eligible sources, L1 projections, relations,
and views each time it is used.

### Frozen evidence pack

A frozen pack records a reproducible snapshot containing selected excerpts or content references,
source and mirror hashes, relationship evidence, view versions, timestamps, and warnings. It is
appropriate for audit, review, or repeatable agent execution.

A paths-and-metadata-only export remains useful as a safe selection manifest, but it must not be
described as self-contained agent context. A context pack intended for execution must either carry
bounded content or contain resolvable references available to the receiving agent.

## 13. Portal and Visualization

Visualization is a presentation of governed state, not the relationship engine itself.

The portal should:

- collapse each source and L1 mirror into one conceptual evidence card by default;
- reveal source/mirror lineage on demand;
- display typed relationships with evidence, confidence, and review state;
- show staleness and invalidation propagation;
- offer task- and audience-specific knowledge views;
- distinguish generated, reviewed, stale, and authoritative artifacts visually;
- build dynamic or frozen context packs within explicit content budgets;
- avoid an unreadable graph hairball through clustering, filters, and progressive disclosure.

The portable metadata-only catalog remains a safe interface. A content-inclusive portal is local
and inherits the sensitivity and redistribution limits of the underlying corpus.

## 14. Profiles

Profiles should define behavior rather than encourage note creation. The profile contract should
own:

- source roots and admission policy;
- format and extraction policy;
- privacy, retention, licensing, and publication rules;
- relationship vocabulary and deterministic rules;
- entity-resolution boundaries;
- knowledge-lens definitions;
- review and persistence gates;
- context budgets and permitted export modes;
- portal views and validation tasks.

Legacy note templates and MOC/entity-page requirements should be removed or migrated into optional
view definitions. Domain folders may remain useful for authoritative sources and operational
artifacts, but they are not a reason to create one Markdown note for every conceptual object.

## 15. Security, Rights, and Governance

MirrorArc's no-data rule remains non-negotiable for this repository. Public examples may contain
only synthetic material or genuinely public, permissively licensed artifacts with documented
provenance and licence terms.

Official publication does not automatically mean redistributable. Non-official public material is
also not safe to commit merely because it is downloadable. When rights are unclear, MirrorArc may
record a metadata-only reference or use the file in an operator-controlled, uncommitted validation
workspace if policy allows; it must not add the content to the public example.

The relationship ledger and derived views may reveal sensitive associations even when they do not
copy entire documents. They must remain inside the source collection's trust boundary and inherit
its access, retention, and disposal policy.

Secrets, credentials, tokens, personal data, and proprietary records never belong in this
repository, its examples, generated portal, logs, screenshots, tests, or history.

## 16. Validation Contract

MirrorArc is not complete when code exists. It is complete when the product behavior is proven on
a complex, rights-cleared source collection.

Required test families are:

1. **L1 correctness:** identity/cardinality, source preservation, conversion warnings, idempotence,
   move/delete behavior, and recovery;
2. **anti-proliferation:** reject unexplained user-facing Markdown and prevent sibling mirrors or
   automatically accumulated knowledge notes;
3. **relationship evidence:** deterministic and proposed edges, evidence anchors, provenance,
   review, rejection, and invalidation;
4. **L2 lifecycle:** many-to-few generation, pin/review, source-change staleness, replacement
   candidates, and promotion to authoritative source;
5. **incremental dependency behavior:** one source change recomputes only its affected subgraph and
   views;
6. **context assembly:** dynamic freshness, frozen reproducibility, content budgets, and source
   citations;
7. **portal behavior:** navigation, relationship inspection, view status, context building,
   accessibility, responsive layout, and sensitive-content boundaries;
8. **safety and rights:** no-data, path, secret, PII, licence, provenance, and public-export gates;
9. **scale:** a mixed-format Ontario electricity corpus large and varied enough to expose lifecycle,
   relationship, retrieval, and UI failures.

The binding execution sequence and acceptance matrix live in
[`PRODUCT_IMPLEMENTATION_PLAN.md`](PRODUCT_IMPLEMENTATION_PLAN.md).

## 17. Current Implementation Assessment

The repository already provides a substantial deterministic foundation:

- source-preserving Office/PDF and repository mirroring;
- manifests, hashes, lifecycle states, audits, and annotation-sidecar protections;
- journaled changed-file processing, replay, locking, reconciliation, and full recovery sync;
- profiles, catalog generation, review metadata, benchmarks, safety scans, and an Ontario
  electricity demonstration portal.

The local working tree includes the relationship/provenance ledger, dependency invalidation,
reviewed-view lifecycle, context packs, migration inventory, and a portable Catalog. These are
implemented capabilities; historical validation does not prove the current dirty tree.
The current [Trustworthy Context plan](TRUSTWORTHY_CONTEXT_EXECUTION_PLAN.md) requires fresh
local gates, task-retrieval measurements, export-integrity checks and a separate review handoff.
Empirical model-quality evaluation requires explicit endpoint/data/spend authorization.

## 18. Finite Product Direction

Development proceeds in this order:

1. converge the product, methodology, profile, sync, and agent contracts;
2. define migration and compatibility boundaries;
3. enforce L1 identity and anti-proliferation invariants;
4. implement the relationship and provenance ledger;
5. connect journal events to dependency invalidation;
6. implement L2 knowledge views and their lifecycle;
7. implement dynamic and frozen context assembly;
8. update the portal and visualization;
9. migrate templates and the Ontario example;
10. validate the completed product against an expanded mixed-format Ontario electricity corpus.

The following remain outside this goal unless required to satisfy an acceptance criterion:

- vector embeddings or a vector database;
- hosted SaaS;
- multi-user real-time collaboration;
- a desktop shell;
- an Obsidian plugin;
- broad cloud connector development;
- package-part incremental extraction;
- autonomous promotion of generated knowledge into authority;
- public deployment of unreviewed or rights-uncleared corpus content.

## 19. Principal Risks

| Risk | Severity | Mitigation |
| --- | --- | --- |
| L2 becomes one more document factory | Critical | Many-to-few lenses, ephemeral default, explicit persistence gate |
| A generated view is mistaken for authority | Critical | Visible state, citations, provenance, and promotion boundary |
| Semantic edges become unexplained model opinions | Critical | Evidence anchors, hashes, generation records, confidence, and review |
| Source events are mistaken for complete change truth | Critical | Journal plus mandatory reconciliation and full recovery sync |
| Native Markdown is duplicated without value | High | Register readable sources directly unless isolation requires a projection |
| Reviewed views are silently replaced | High | Mark stale, preserve approved version, generate a candidate |
| Relationship or view recomputation becomes corpus-wide | High | Dependency-led invalidation and structural performance tests |
| Portal presents a graph hairball | High | Collapse source/mirror pairs, cluster, filter, progressive disclosure |
| Public sample violates rights or privacy | Critical | Licence/provenance gate, metadata-only references, no-data scan |
| Context packs leak content | Critical | Explicit dynamic/frozen modes, budgets, sensitivity labels, local-only review |
| Architecture work never closes | Critical | Finite plan, stage exits, Ontario end-to-end finish line |

## 20. Product Implication

The strongest product position is not “AI documentation” and not “chat with your files.” It is:

> **MirrorArc minimizes the documentation a team must maintain while maximizing the source-backed
> knowledge that people and agents can retrieve, interpret, and trust.**

This direction preserves MirrorArc's strongest existing differentiators—source authority,
provenance, lifecycle, anti-proliferation, linking-first retrieval, and local-first operation—while
removing the curated-wiki compromise that produced the Ontario example's excess Markdown.

## 21. Bottom Line

MirrorArc should preserve original records, produce one governed L1 projection for each opaque
source, express relationships as evidenced data, render a small number of L2 knowledge views, and
assemble context for a purpose.

It should not blindly create Markdown because Markdown is cheap. Markdown is a projection format;
the evidence-backed relationship model is the connective tissue; knowledge views are disposable
reading surfaces; authoritative records remain the source of truth.

The architecture is now decided. Completion requires implementing it and proving the complete
loop—ingest, mirror, connect, interpret, invalidate, assemble context, and navigate—against a much
larger mixed-format Ontario electricity corpus in the portal.

## References

- Microsoft MarkItDown: https://github.com/microsoft/markitdown
- Materialized View pattern: https://learn.microsoft.com/azure/architecture/patterns/materialized-view
- CQRS pattern: https://learn.microsoft.com/azure/architecture/patterns/cqrs
- W3C PROV-O: https://www.w3.org/TR/prov-o/
- W3C Web Annotation Data Model: https://www.w3.org/TR/annotation-model/
- MirrorArc product contract: `docs/PRODUCT.md`
- MirrorArc sync specification: `docs/SYNC_SPEC.md`
- MirrorArc profile schema: `docs/PROFILE_SCHEMA.md`
