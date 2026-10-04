# Trustworthy Context — Execution Plan

Date: 2026-09-18

Status: implemented; final local evidence is in the developer handoff. Planning-session acceptance has not started.

Owner: cz1993. Development: separate Codex session. Review: originating planning session.

Repository: `/Users/cz/workspaces/cz1993/MirrorArc`

Related documents:

- [Development kickoff](prompts/TRUSTWORTHY_CONTEXT_EXECUTION_KICKOFF.md)
- [Post-development review](TRUSTWORTHY_CONTEXT_REVIEW.md)
- [Product contract](PRODUCT.md), [whitepaper](MIRRORARC_WHITEPAPER.md)
- [Earlier implementation baseline](PRODUCT_IMPLEMENTATION_PLAN.md)
- [Earlier repository-intelligence proof](CODE_INTELLIGENCE_EXECUTION_PLAN.md)
- [Existing benchmark contract](AGENT_READINESS_BENCHMARK.md)

## 1. Outcome and scope

Make MirrorArc's context exports trustworthy, task-relevant, measurable, and understandable to
a new user. Preserve the source-to-projection-to-ledger-to-view architecture. This is an extension
of the current working tree, not a rewrite or restart of the August implementation.

Required work: reproduce and close evidence/policy/resource-boundary defects; implement a compact
evaluation loop; add deterministic task-driven retrieval through existing context assembly;
improve the first-use and Catalog journey; validate the complete local package; prepare a review
handoff. Required experiments: bounded CodeGraph upgrade and difficult-document extraction
comparisons. Their adoption is conditional on results, not a predetermined requirement.

Completion states are distinct:

1. **Implemented:** required changes exist, with focused verification.
2. **Locally validated:** complete local gate and clean-wheel proof pass for a fingerprinted tree.
3. **Accepted:** this planning session reviews the evidence and current tree and accepts shipment.
4. **Shipped:** the owner-approved consolidated PR is merged, with its resulting SHA recorded.

No development session may label itself independently accepted. Local proof does not establish
hosted, Linux, production, universal retrieval superiority, or deployment proof.

## 2. Operator policy and authority

- All development and tests are local. No intermediate pushes, per-workstream PRs, hosted CI
  dispatches, ADS review loops, automatic reviewer sessions, or hosted-CI acceptance dependency.
- No commit, push, merge, publication, deployment, tag, global installation, or remote setting
  change during development. Prepare one final shipment only after planning-session acceptance.
- Preserve the existing dirty tree, including tracked edits, deletions, and untracked modules.
  Do not reset, stash, discard, broadly reformat, or reconstruct it from HEAD. An ordinary clean
  worktree from HEAD would omit the current implementation; do not use that as the baseline.
- Use disposable copies and isolated dependency environments for tests and tools. Downloading
  verified open-source dependencies for local tests is allowed; no global provider installation.
- No private corpus ingestion, paid model calls, cloud document upload, or external telemetry is
  newly authorized by this plan. If measured model evaluation needs an endpoint, obtain explicit
  endpoint/data/spend approval; continue other work while that prerequisite is unresolved.
- The planning session remains a planning/review session. Do not start implementation there or
  create another task automatically from the kickoff document.

## 3. Baseline and findings

At planning time: branch `codex/knowledge-projection`; HEAD
`15ce475a5077ce9d048a3f38a9a832a08976ffd9`; extensive existing uncommitted implementation. Capture
fresh state before work. A HEAD SHA alone is not a fingerprint of this batch.

The September review passed diff formatting, no-data scan, and template-copy checks. It did not
rerun the full suite, fresh-wheel proof, or browser journeys. Earlier recorded test totals are
historical evidence only. Two defects were reproduced using isolated execution of the actual
helper functions, not the entire installed product; turn these into public-path regressions.

| ID | Observed issue | Initial location | Evidence level |
| --- | --- | --- | --- |
| TC-01 | Merged line ranges retain only the first excerpt/hash, overstating included evidence | `code_intelligence/service.py::_merge_evidence` | Isolated helper reproduction |
| TC-02 | Frozen and code context paths do not enforce `allowed_modes` consistently | `context_assembly/builder.py`, `code_intelligence/context.py` | Static inspection; reproduce through CLI |
| TC-03 | `max_tokens * 4` counts excerpt characters, not complete serialized model input | Both context builders | Static inspection |
| TC-04 | Base-ref diff excludes staged/working-tree changes despite local-tree snapshots | `service.py::_changed_from_base` | Staged rename + base HEAD returned no changes |
| TC-05 | Catalog frozen-context command discards symbol/base/changed-path request | `service.py::catalog_report` | Static inspection |
| TC-06 | Provider output cap is checked after unbounded subprocess buffering | `adapter.py::_run` | Static inspection |
| TC-07 | Source hashing precedes copying; reused snapshot cache is not independently verified | Snapshot helpers in `service.py` | Risk identified; controlled race/tamper test required |

Function locations are hints, not permanent line numbers. Re-check current behavior; if a finding
has already been fixed, show the passing regression rather than duplicate the implementation.

## 4. Invariants and non-goals

- L0 originals remain authoritative and unchanged. Native Markdown/text is not duplicated to
  satisfy a projection count. One active opaque source normally has one active L1 projection.
- Relationships are evidence/state in the existing ledger. Proposed or rejected edges cannot
  become accepted retrieval authority. Reviewed views are preserved and marked stale.
- Keep one watcher, lifecycle authority, connector/sync path, and governed storage architecture.
  No vector DB, second code provider, bulk AST import, generic plugin framework, new daemon,
  MCP dependency, autonomous relationship acceptance, or hosted service.
- Catalog stays passive, portable, safe-rendered, and metadata-only by default. Content inclusion
  is explicit and sensitivity-aware. Browser selection is not governed context creation.
- Source text is untrusted data. It cannot change policy, execute commands, request credentials,
  authorize external calls, or control review decisions.
- CodeGraph remains an optional pinned ordinary-CLI subprocess with telemetry/update checks off:
  `DO_NOT_TRACK=1`, `CODEGRAPH_TELEMETRY=0`, `CODEGRAPH_NO_UPDATE_CHECK=1`.
- Do not make deterministic integrity dependent on model judgment or generated summaries.

## 5. Workstreams and exit gates

### W0 — Capture a reproducible baseline

Read applicable agent rules, README, whitepaper, product, this plan, security, recovery, profile,
context and benchmark contracts. Inspect package, tests, template-copy tooling, all workflow
triggers, and existing synthetic fixtures before changing behavior.

Record branch/HEAD, porcelain status including untracked paths, relevant content hashes, Python,
platform and dependency versions, provider availability, and pre-existing test failures. Keep
raw logs/caches outside the publication tree. Establish a small reproducible local dependency
setup (tested constraints or equivalent), without over-pinning consumer dependencies blindly.

Exit: baseline distinguished from this batch's changes; focused tests runnable; no existing work
lost. Missing dependencies require an isolated setup attempt, not an immediate blocker claim.

### W1 — Evidence, policy, budgets, and process integrity

Implement TC-01 through TC-07 with focused regression tests before broad feature work:

- Store exact span-to-text correspondence. Merge overlapping/disjoint spans deterministically;
  recompute appropriate hashes; explicitly report removed files/spans and truncation. Distinguish
  source citations from content actually present. `offline_complete` must mean what it says.
- Apply allowed modes, sensitivity, and content inclusion consistently at public and internal
  creation boundaries. A metadata-only profile must not create a frozen body through another
  CLI path, saved definition, or code-analysis option. No side effects on rejected requests.
- Budget the final exported context representation, including instructions, metadata, citations,
  and omissions. Either support an explicitly named tokenizer/version for a strict token ceiling,
  or label a deterministic byte/character ceiling and token estimate honestly. Do not advertise
  a model-independent hard token guarantee. Handle overhead-only overflow without invalid output;
  report effective limits and method. Include non-ASCII/code and tiny-budget cases.
- Define base semantics explicitly. Preserve compatibility where possible: distinguish committed
  base-to-HEAD changes from staged/unstaged/untracked changes. Whichever mode is selected must
  match the analyzed tree. Handle rename/deletion/binary/ignored paths with visible omissions;
  deleted files cannot be cited as current source bodies.
- Preserve the exact analysis selection in Catalog context actions, safely quoting paths and
  arguments, or reuse its stored governed definition. Test spaces and option-like input.
- Bound stdout/stderr while reading, enforce timeout, clean up child processes on supported
  platforms, and avoid publishing partial invalid results. Test excessive output and a hung child.
- Verify copied snapshot content against its recorded tree identity; detect mutation during copy
  and cache tampering. Use a bounded retry/fail-stale path, not an infinite reconciliation loop.
  Traverse excluded directories efficiently and keep resource ceilings explicit.

Exit: public-path regressions demonstrate correct excerpts, denied policy bypasses, honest budget
semantics, correct change scope, preserved selection, bounded execution, and verified snapshots.
Update affected profile/security/recovery contracts and historical proof qualifications.

### W2 — A compact, reusable evaluation loop

Extend `benchmark.py` and the existing benchmark contract; do not create a second results system.
Use a small fixed pack (initial target 12 tasks) across three small synthetic/rights-cleared
collections: mixed documents, conflicting/revised documents, and the existing synthetic code
repository. Reuse existing fixtures; no large corpus or language matrix. Cover answer, reconcile,
update, audit, consolidation, insufficient-evidence, and document-instruction attacks.

Before tuning, fix task IDs, expected evidence/answers, source revisions, scoring rules, and a
small held-out subset. Compare raw sources, plain conversion, and governed MirrorArc context
with the same model, prompt, tool permissions and budget where comparable. Record unsupported
input differences rather than silently giving one mode privileged access. Separate deterministic
retrieval tests from model outcome evaluation; manual invented results are never measured results.

Record correctness (existing 0–2 scoring), citation accuracy, evidence coverage, stale-evidence
use, abstention, privacy/prompt-safety failures, latency, token count, and human corrections. Use
deterministic checks for hashes/spans/policies and human calibration for semantic grading. Report
per-task outcomes and repeats for stochastic runs; do not claim significance from a tiny sample.

Promptfoo is an optional dev-only runner if it reduces code, never a runtime dependency. Disable
unneeded external features; model calls require the approval in section 2. Keep raw private result
packs outside the repo and preserve current no-data restrictions; commit only allowed synthetic
fixtures and sanitized aggregate evidence.

Exit: runnable deterministic benchmark, reproducible task manifest, baseline results and honest
model-evaluation status. If endpoint/spend approval is unavailable, label empirical agent outcome
evaluation pending, with an exact rerun command; do not falsely claim superiority or full acceptance.

### W3 — Task-driven retrieval through existing context assembly

Implement deterministic lexical/heading retrieval using SQLite FTS5/BM25 in the existing derived
storage architecture, not a second authoritative database. Probe FTS5 availability and give a
clear supported fallback/error. Index allowed authoritative text/L1; preserve source identity,
hashes, provenance, sensitivity, and freshness. Index schema/version is disposable and rebuildable.

Add a task/query input to existing context commands rather than a parallel command family. Rank
matches with stable tie-breaking, deduplicate source identities, and expand only through permitted
current deterministic/accepted relationships. Bound hops, candidates, files, and export size;
prevent cycles. Never let a retrieval cache elevate rejected/proposed/stale edges into authority.

Show why each result was selected, source spans, score/ranking method, freshness, and exclusions.
Propagate changed/deleted sources via existing invalidation. Do not offer opaque confidence as
truth. Preserve compatibility for existing saved contexts and explicit selections.

Exit: same task/tree yields stable selection; cache deletion rebuilds equivalent results; source
change invalidates affected selections; held-out evaluation compares retrieval to the baseline.
If gains are absent, report that result and keep the old default or gate the new mode as opt-in.

### W4 — One understandable user journey

Consolidate README/quickstart/INDEX and the existing synthetic-code walkthrough around:
choose a task → inspect selected evidence → understand warnings/omissions → export context.
Keep the existing short optional `code doctor` / `code analyze` / `catalog --html` flow.

Catalog must explain selected/not selected, included/reference-only, source revision/freshness,
mode and sensitivity. Preserve the request in the next action. No backend execution or network
fetch in HTML. Avoid a UI rewrite: extract shared policy/report semantics only when needed.
Remove stale future-tense claims and outdated hubs/entity-page benchmark descriptions.

Exit: verify three browser journeys (setup/empty, useful current selection/export, stale/failure)
at desktop and narrow width, including keyboard focus, long paths, safe rendering, and metadata
versus content-inclusive output. Record screenshots and exact commands. An agent-run walkthrough
is not evidence of an independent novice usability study; obtain operator feedback at review.

### W5 — Evidence-gated upstream experiments

1. **CodeGraph:** compare pinned v1.5.0 with researched v1.6.0 in disposable installations on the
   same small repository. Verify machine-readable contracts, symbol/call/impact/affected-test
   results, edit/rename/delete refresh, cache recovery, telemetry suppression, and failure behavior.
   Re-verify upstream installer/checksums before documenting a new pin. Promote only on a green
   contract suite and concrete benefit; otherwise retain v1.5.0 with reasons. No agent installer.
2. **Docling:** compare with current MarkItDown on a handful of synthetic difficult PDFs/tables/
   scans. Record extraction errors, source/page anchors, time, peak memory where measurable,
   package/model versions, licensing, and model-download/network behavior. A useful measured
   result permits a narrow optional converter path through existing L1 lifecycle; otherwise
   record a no-adoption decision. Never change the default merely because the tool is popular.
3. **PageIndex:** design reference or isolated optional comparison only. Its local SDK may use a
   remote model. Runtime integration and model-dependent retrieval authority are out of scope.

Timebox each primary experiment to one representative comparison and at most one bounded fix
per concrete failure hypothesis. If upstream remains unsuitable, record evidence and stop that
experiment without expanding to another provider. Required outcome is a decision, not adoption.

Exit: versioned comparison records and adopt/defer decisions; promoted changes rerun impacted
gates. No unsupported claims about untested platforms or extractors.

### W6 — Final local validation and developer handoff

Run focused tests while iterating; run the complete repository gate near completion, not after
every edit. Derive local parity from the current CI/release scripts, without dispatching them.
Minimum final checks:

- `git diff --check`
- `python scripts/no_data_scan.py`
- `python scripts/sync_template_copies.py --check`
- Python compilation and POSIX shell syntax checks for applicable files.
- Full `python -m pytest` with exact counts, duration, failures/skips, and dependency versions.
- Template lint and regenerated disposable Ontario example lint using the installed runtime and
  each copy's `tools/lint_vault.py`; record all warnings. Do not overwrite example source files.
- Scan generated artifacts separately for no-data/provenance safety.
- Build wheel in a temporary output directory, install into a fresh Python 3.11 environment,
  run dependency consistency checks and CLI help/initialization smoke outside the source checkout.
- Fresh-wheel journey: sync source → select task → inspect correct current evidence → create
  allowed context → view portable Catalog → mutate synthetic source → detect staleness → rebuild.
- Real pinned-provider smoke and cache-delete/rebuild; required W4 browser checks; W2/W3 evaluation.
- Hash originals before/after; confirm no global configuration edits, telemetry, tracked caches,
  secrets, private results, or unexpected network requests.

Report host/platform truthfully. Local Linux validation may use an already available disposable
container/runtime; do not claim Linux proof if unavailable or make hosted CI a substitute.

Create `docs/TRUSTWORTHY_CONTEXT_HANDOFF.md` only when actual evidence exists. Include W0–W6 status,
TC-01–TC-07 regressions, changed-file scope, test commands/results, benchmark outcomes, dependency/
provider versions, UI evidence paths, original-source preservation, known limitations, unresolved
approvals, and precise reproduction instructions. Include SHA-256 manifest of intended shipping
files (including untracked additions and a deleted-path list) outside generated output; record
its digest in the handoff. Exclude the handoff/manifest themselves from self-referential hashing
and state that exclusion. Do not record credentials or private source bodies.

Exit: handoff ready for this planning session, not self-approved or shipped. A failed required
gate stays failed with concrete evidence; no softened criteria to obtain a green summary.

## 6. Post-development review and single shipment

This session uses [the review checklist](TRUSTWORTHY_CONTEXT_REVIEW.md), inspects the live tree
independently, and records acceptance or bounded corrections. Development addresses corrections
locally; review repeats on the new tree fingerprint. No GitHub round trips are needed.

After acceptance, the operator activates final shipment. Reconcile exact intended additions,
edits and deletions across the old dirty baseline and this batch; do not blindly stage the entire
workspace. Preserve owner identity and author one consolidated PR, then merge the accepted head.
No history rewrite or force-push is implied. Record branch/base/head/merge SHAs and final status.

Before any push, inspect live remote state and local workflow triggers. At planning time:

- `ci.yml` runs on PR events and pushes to main;
- `pages.yml` can deploy on relevant main changes and manual dispatch;
- `release.yml` runs on version tags.

Hosted checks are not required by this project policy, but an existing remote protection may still
enforce them. Do not falsify status, use an admin bypass, or weaken remote rules automatically.
If zero hosted runs are required, prepare a narrowly scoped manual-only workflow change for
review before shipping. If protections or deployment intent are unresolved, stop before the push
and ask the owner to choose. Do not rely on skip markers to suppress every workflow. Code PR merge
does not imply permission for Pages deployment, release tags, package publication, or global install.

## 7. Research basis and adoption discipline

Sources reviewed 2026-09-18; re-check contracts at implementation time, not floating versions at
runtime. Upstream claims are experiment hypotheses, not MirrorArc benchmark results.

- [CodeGraph v1.6.0](https://github.com/colbymchenry/codegraph/releases/tag/v1.6.0): incremental
  index correctness, graph fixes, and WAL recovery justify a compatibility experiment.
- [SQLite FTS5](https://www.sqlite.org/fts5.html): mature BM25/snippet functionality supports a
  small deterministic lexical baseline, not a new external service.
- [Promptfoo](https://github.com/promptfoo/promptfoo): optional evaluation/red-team runner.
- [Docling](https://github.com/docling-project/docling): structured extraction and OCR candidate.
- [PageIndex](https://github.com/VectifyAI/PageIndex): hierarchical/vectorless retrieval reference;
  local storage must not be confused with offline model inference.
- [Context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents):
  selective just-in-time context informs the task-first direction.
- [Official Codex prompting guidance](https://learn.chatgpt.com/docs/prompting): kickoff specifies
  the outcome, relevant repository context, constraints, and verification evidence explicitly.

## 8. Progress ledger

Update evidence/status only after work occurs. Use pending, active, passed, failed, or conditional;
include a reason and evidence path for conditional work. Never pre-fill passing results.

| Workstream | Initial state | Evidence |
| --- | --- | --- |
| W0 baseline | complete | Initial dirty status/diff/hashes and 14-pass baseline retained; see handoff. |
| W1 integrity | implemented / locally checked | TC-01–TC-07 public regressions, streaming/snapshot/byte-budget checks and actual provider proof. |
| W2 evaluation | deterministic complete; empirical pending | Fixed 12-task pack before tuning; model metrics null without endpoint/data/spend approval. See results. |
| W3 retrieval | complete, opt-in | Existing FTS5 store, stable/current accepted selection, rebuilds and invalidation; coverage 0.55 → 0.90, held-out tc11 regression retained. |
| W4 user journey | implemented / browser checked | Fresh-wheel empty/current/stale/failure, desktop/narrow and keyboard proof; independent novice feedback pending. |
| W5 upstream experiments | complete, no adoption | CodeGraph 1.5.0 retained; Docling missing offline models after one retry; MarkItDown scan/column limitations recorded. |
| W6 final local proof/handoff | developer evidence supplied; not accepted | See [handoff](TRUSTWORTHY_CONTEXT_HANDOFF.md), exact final logs and file manifest. Planning review and shipment checkpoint remain pending. |
| Planning-session acceptance | pending | — |
| Single GitHub shipment | not authorized to start | — |

Developer evidence: [handoff](TRUSTWORTHY_CONTEXT_HANDOFF.md), [benchmark results](TRUSTWORTHY_CONTEXT_RESULTS.md),
[upstream decisions](TRUSTWORTHY_CONTEXT_EXPERIMENTS.md). No reviewer acceptance is implied.
