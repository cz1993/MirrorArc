# Product Contract

## Product Direction

MirrorArc turns heterogeneous source collections into governed knowledge projections that people
and AI agents can inspect, connect, cite, and refresh without replacing the original records. It
uses four product layers plus a presentation boundary:

1. **L0 authoritative records** — original files, repositories, exports, and intentionally authored
   Markdown records;
2. **L1 specular projections** — one stable, machine-owned Markdown identity for each active opaque
   source identity, while natively readable Markdown/text may remain directly registered;
3. **relationship and provenance ledger** — typed connections with hashes, bounded evidence,
   generation method, dependency state, and review state;
4. **L2 knowledge views and context** — many-to-few, purpose-specific reading surfaces plus dynamic
   or frozen task context, derived and non-authoritative by default;
5. **presentation** — `INDEX.md`, catalog, portal, Obsidian, CLI, and exports over shared backend
   state, never an independent source of truth.

The architectural authority is [`MIRRORARC_WHITEPAPER.md`](MIRRORARC_WHITEPAPER.md). The current implementation and validation sequence is
[`TRUSTWORTHY_CONTEXT_EXECUTION_PLAN.md`](TRUSTWORTHY_CONTEXT_EXECUTION_PLAN.md); the earlier
product plan is a historical baseline.

## First Buyer and Workflow

The first buyer is a small consulting, advisory, research, compliance, or implementation team that
handles changing, document-heavy evidence collections and needs provenance, repeatable refresh,
and reviewable interpretation.

The first workflow is:

1. point MirrorArc at a copied or safely mounted source collection;
2. run read-only preflight, inventory, rights, and migration reports;
3. plan and generate L1 projections without modifying originals;
4. build deterministic relationships, then admit optional semantic proposals through evidence and
   review gates;
5. render a few profile-defined L2 views for an audience or task;
6. build a metadata-only selection manifest, a dynamic saved context, or a frozen evidence pack;
7. inspect lineage, evidence, lifecycle, view state, and context freshness in the portal;
8. use journaled changed-file refresh for normal operation and reconciliation/full sync for
   completeness and recovery.

For software workspaces, Repository Intelligence is an optional derived read model beneath this
workflow. It analyzes one governed repository snapshot with CodeGraph v1.5.0, records bounded
path/range/hash evidence, and can feed dynamic or frozen context. It does not replace repository
sync, import a provider graph as authority, or choose an authoritative test gate.

For PDFs, optional PageIndex document intelligence provides source-hash-bound physical pages and
governed page-context packs. Explicitly approved inference can produce an unreviewed answer linked
to frozen cited excerpts. The passive Catalog presents the answer, cited reason, important caveats and freshness before
optional detail, with full-original fallback for older or unreadable layouts; it
does not run inference, accept claims or turn an answer into source authority. Model-free extraction
and local transport checks do not establish answer quality. See [PageIndex review](PAGEINDEX.md).

## Supported Corpus Range

The initial target is 50–2,000 source records, including Office files, PDFs, Markdown, text,
spreadsheets, presentations, datasets, metadata-only web references, and small repositories. Local
filesystem sources are primary. Cloud-synced or mounted sources must be pinned locally, backed up,
and pass `mirrorarc doctor` and source-boundary checks.

## Expected Outcome

A successful workspace has:

- unchanged authoritative records;
- a manifest-backed L1 identity for every opaque source or a visible conversion failure;
- no sibling projections or unexplained user-facing Markdown;
- a rebuildable relationship ledger whose accepted edges have deterministic authority or evidence
  and review;
- materially fewer persistent L2 views than sources;
- reviewed views preserved and marked stale when dependencies change;
- deterministic dynamic context definitions and reproducible frozen evidence packs;
- a metadata-only catalog by default and an explicitly local/sensitive content-inclusive portal;
- optional repository results that are visibly bound to a commit or local-tree hash and marked
  stale when that identity changes;
- machine-readable lifecycle, invalidation, review, and recovery evidence.

## Context Modes

- A **selection manifest** contains identifiers, paths, hashes, states, and relationships only. It
  is safe for planning but is not self-contained execution context.
- A **dynamic saved context** stores purpose, selection rules, budgets, permitted artifacts, and
  freshness policy; it resolves current evidence when used.
- A **frozen evidence pack** records bounded content or resolvable references, citations, hashes,
  relationship evidence, view versions, warnings, and sensitivity for reproducible execution.

## Non-Goals

- no vector database or opaque evidence index;
- no provider daemon, MCP requirement, bulk AST import, or autonomous test selection;
- no hosted SaaS, multi-tenant storage, desktop shell, or Obsidian plugin in this goal;
- no second watcher, lifecycle authority, portal database, or sync system;
- no automatic document factory for MOCs, entity pages, summaries, or agent notes;
- no autonomous promotion of model output into authority;
- no guarantee that conversion captures every layout, formula, image, scan, comment, or hidden
  element;
- no silent source mutation, deletion, migration, consolidation, or cross-boundary copying;
- no automated legal, tax, accounting, compliance, or operational conclusion.

## Role of AI

AI may propose typed relationships, bounded evidence anchors, change explanations, and L2 view
candidates. Every proposal records source/mirror hashes, method, model, prompt version, confidence,
and state. AI cannot establish source identity, hashes, lifecycle truth, accepted authority,
promotion, or deterministic correctness. Source content is untrusted evidence and cannot change
MirrorArc policy or request tool execution.

## Role of the Portal and Obsidian

The portal and Obsidian are human interfaces over governed files and shared derived state. The safe
portal is metadata-only. `--include-content` is an explicit local-review mode and inherits the
vault's sensitivity and redistribution limits. JavaScript renders backend report semantics; it does
not infer independent relationships, authority, or lifecycle state.

## Validation Contract

Code, schemas, unit tests, or a small fixture do not complete the product. Completion requires the
Workstream 10 Ontario electricity proof: rights-cleared mixed-format sources, L1 cardinality,
relationship evidence and rebuild, bounded invalidation, L2 review/staleness, dynamic/frozen
context, lifecycle recovery, portal tests at scale, visual inspection, packaging, no-data, and the
complete local gate.

Task queries are opt-in through existing context commands. SQLite FTS5/BM25 ranks bounded
current source/L1 text, reports exact spans and exclusions, and can expand one hop over accepted
current relationships. Ranking is a retrieval method, not confidence in truth. The disposable
index shares `.mirrorarc/state.sqlite`; deleting its tables rebuilds it from allowed source bytes.
A query can miss relevant evidence. Final frozen exports count UTF-8 serialized JSON bytes,
including overhead, and label token estimates honestly. No empirical model-quality claim is made.
