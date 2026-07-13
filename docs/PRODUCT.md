# Product Contract

## Product Direction

Vaultwright turns heterogeneous source collections into governed, profile-driven knowledge
workspaces that humans and AI agents can inspect, navigate, cite, and refresh without replacing the
original records. The canonical v1 direction now adds journaled changed-file materialization:
after an initial baseline, normal steady-state refresh should process event-identified candidate
sources, while full sync remains the recovery and verification path.

Current execution order is validation-first: run a real external corpus through the core mirror,
catalog, benchmark, recovery, and handoff flow before expanding Obsidian adapters, local indexes,
or indexed Explorer. One bounded Stage 3 exception exists: a scan-on-open, index-free,
localhost-only, read-only Guided Knowledge Map/Navigator is implemented as the non-Obsidian
front-door instrument for orientation and comprehension testing. Its implementation does not
complete or bypass external validation. The hard stop, proof boundary, and pivot criteria are tracked in
[`docs/VALIDATION_GATE.md`](VALIDATION_GATE.md).

The first paid workflow remains consulting and implementation work, but the v1 architecture is no
longer a single business-operations folder template. The accepted v1 direction is documented in
[`docs/adr/0001-profile-driven-v1-architecture.md`](adr/0001-profile-driven-v1-architecture.md)
and the release gates are tracked in [`docs/V1_FINISH_LINE.md`](V1_FINISH_LINE.md).

## First Buyer

Vaultwright's first buyer is a small consulting, advisory, or implementation team that handles
document-heavy client onboarding, operational audits, funding-readiness work, compliance reviews,
or recurring operating-system cleanup.

The first buyer is not "all small businesses." Owner-operators may benefit later, but consulting
teams are the better wedge because they already understand engagement boundaries, provenance,
source preservation, repeatable delivery, and client trust.

## First Workflow

The first workflow is:

1. Point Vaultwright at an existing client document collection.
2. Produce a non-destructive inventory and sync plan.
3. Generate mirrors for supported files without modifying originals.
4. Run a read-only conversion spot-check report for unsupported, stale, conflicted, risky, or
   potentially low-quality conversions.
5. Generate Markdown/HTML catalog gateways for operator, reviewer, and agent orientation.
6. During the Stage 3 proof, optionally compare that catalog with the read-only Navigator's curated
   entry points and reading trails; do not require Obsidian, an evidence index, or a global graph.
7. If the customer uses Microsoft 365, run a read-only Microsoft 365/Copilot handoff readiness
   report before moving derived content into approved tenant boundaries.
8. Record metadata-only human review decisions against generated mirrors, catalogs, and handoff
   reports so approvals are tied to artifact hashes.
9. Create a small number of curated hubs, entity pages, and explicit navigation trails where a
   stable reading order helps a defined audience complete a task.
10. Refresh the workspace over time with auditable sync/status output, including structured
   `--json` evidence from `sync`, `status`, and `doctor` for agents and pilot records.
11. After Stage 1B, use journaled changed-file materialization for normal steady-state refresh and
    full sync for recovery, reconciliation, and verification.

## Supported Corpus Range

Initial target corpus:

- 50 to 2,000 source files.
- Office files, PDFs, markdown, plain text, spreadsheets, decks, and small repositories.
- Single-client or single-engagement workspace.
- Local filesystem source; cloud-synced or mounted/network folders are acceptable only when files
  are pinned locally, backed up, and checked with `vaultwright doctor` before production sync.

Out of scope for the first release:

- Multi-tenant hosted storage.
- Enterprise DMS replacement.
- Unbounded network crawls.
- Bulk email/mailbox ingestion.
- Fully automated legal, tax, accounting, or compliance conclusions.

## Expected Outcome

A successful first workflow produces:

- original files unchanged;
- full sync available as baseline and recovery mode;
- future journaled changed-file materialization state kept local and derived, never authoritative;
- generated mirrors under `_mirrors/`;
- repo mirrors under the active profile's `repo_notes_dir` (`80_sources/repos/` in the packaged
  business-operations profile);
- generated `CATALOG.md` and `CATALOG.html` inventory gateways;
- source/repo manifests, audit events, and lifecycle status reports;
- a Microsoft 365 handoff readiness report when the target workflow involves SharePoint, OneDrive,
  Copilot Studio, Dataverse, or Copilot connectors;
- a review ledger that records reviewer/status decisions without copying source or mirror bodies;
- aggregate pilot evidence reports that avoid source or mirror content;
- curated hubs for the highest-value document clusters;
- a first-party, Obsidian-independent navigation path that can orient a reader, render governed
  Markdown safely, and explain a bounded logical sequence without persisting an index;
- an agent-readable markdown substrate with source links, frontmatter, headings, manifests, and
  refresh boundaries;
- explicit warnings for unsupported or risky inputs;
- a repeatable refresh procedure.

## Non-Goals

- Not a generic personal PKM or Zettelkasten app.
- Not a hosted SaaS in this open-core repository.
- Not a vector-RAG chatbot over documents.
- Not a filesystem watcher that treats events as authoritative truth.
- Not a public profile marketplace for v1.
- Not an Obsidian plugin for v1.
- Not an unfiltered whole-vault graph or an attempt to make link density stand in for meaning.
- Not permission to build semantic search, an evidence index, or corpus-wide Explorer under the
  name “Navigator.”
- Not a desktop application shell for v1.
- Not a guarantee that conversion output fully represents every table, image, formula, scan, or
  comment.
- Not an autonomous agent that silently rewrites human-maintained business knowledge.
- Not a verifier of Microsoft 365 tenant permissions, sensitivity labels, retention, or Copilot
  indexing behavior.

## Role of Obsidian

Obsidian is an optional reference adapter because it provides local Markdown browsing, links,
properties, graph views, Bases, and Canvas. Vaultwright correctness, basic reader navigation, and
logical-sequence guidance must not depend on Obsidian, Obsidian Sync, community plugins, or a
specific team-deployment model.

## Role of Navigator

Navigator is the first-party comprehension front door. It reads allowed workspace Markdown and
metadata on open into an ephemeral model, then exposes curated starts, bounded maps, safe document
rendering, and explained previous/next trails. `_meta/navigation.yml` is a durable, reviewable path
contract containing references and short navigation guidance, never copied source bodies.

The implemented map is an interactive browser Canvas centered on the selected document and capped
to its one-hop inbound/outbound neighborhood. Complete inbound and outbound link lists provide the
non-visual equivalent and expose neighbors beyond the visual cap. This Canvas is not an Obsidian
`.canvas` file and stores neither layout nor graph state. A new token protects every launch, and
the server enforces the exact loopback Host plus same-origin/cross-site request checks.

The Stage 3 proof is localhost-only, read-only, index-free, and limited to curated trails plus
bounded explicit-link neighborhoods. Corpus-wide query, a disposable SQLite/FTS graph, MCP
exploration, broad graph analysis, and context-pack export belong to the later conditional Explorer
gate. Navigator's value must be measured against ordinary Markdown/catalog use on orientation,
comprehension, provenance/lifecycle recognition, wrong turns, and reviewer correction effort.
The software slice is ready for that comparison; its external evidence is still `Not started`.

## Role of AI

AI may assist with:

- reading generated markdown mirrors as the first operational substrate;
- summarizing generated mirrors;
- proposing curated notes;
- suggesting links and consolidation;
- drafting review checklists;
- answering questions with citations to source-backed notes.

AI must not silently:

- modify original source files;
- delete, move, or consolidate records;
- overwrite human-curated notes;
- make uncited factual claims in durable notes;
- cross client boundaries.

## Agent-Readiness Validation

Vaultwright's long-term value depends on whether agents perform better against governed markdown
than against raw folders or one-off plain markitdown dumps. The benchmark protocol in
`docs/AGENT_READINESS_BENCHMARK.md` defines the evidence needed before this claim is treated as
more than a thesis. `docs/VALIDATION_GATE.md` defines the point where weak benchmark or
self-service evidence must pivot the product away from broad workspace expansion.
