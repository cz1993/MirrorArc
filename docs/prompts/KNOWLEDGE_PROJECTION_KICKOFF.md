# MirrorArc Knowledge-Projection Execution Kickoff

Paste the prompt below into a new Codex session.

---

Work in `/Users/cz/workspaces/cz1993/MirrorArc`.

Create a goal first with this objective:

> Implement the approved MirrorArc knowledge-projection architecture end to end, including L1
> anti-proliferation invariants, the evidence-backed relationship ledger, dependency invalidation,
> L2 knowledge views, dynamic and frozen context assembly, portal integration, safe migration, and
> the expanded Ontario electricity corpus and portal proof required by the implementation plan.

Then pursue that goal continuously until it is genuinely complete or a binding blocker satisfies
the formal blocked threshold. Do not stop after planning, documentation, schemas, partial code,
synthetic unit tests, or a small portal fixture.

Before editing:

1. Read the repository and machine `AGENTS.md` files that apply.
2. Read, in this order:
   - `README.md`
   - `docs/MIRRORARC_WHITEPAPER.md`
   - `docs/PRODUCT_IMPLEMENTATION_PLAN.md`
   - `docs/PRODUCT.md`
   - `docs/SYNC_SPEC.md`
   - `docs/PROFILE_SCHEMA.md`
   - `docs/SECURITY_MODEL.md`
   - `docs/methodology.md`
   - `docs/information-architecture.md`
3. Inspect `git status`, the current branch/upstream, current HEAD, existing worktrees, package
   structure, tests, template-copy rules, and the Ontario example. Preserve all unrelated or
   unfinished user-owned changes. Do not reset or overwrite them.
4. Treat `docs/MIRRORARC_WHITEPAPER.md` as the architectural authority and
   `docs/PRODUCT_IMPLEMENTATION_PLAN.md` as the binding execution sequence and finish-line matrix.
5. Verify current code before assuming an implementation gap. Reuse the existing source mirror,
   journal, lifecycle, catalog, review, profile, and safety foundations.

Execute Workstreams 0 through 10 in order. Keep at most one workstream in implementation at a time
unless two changes are demonstrably independent and cannot create contract or shared-state drift.
After each workstream:

- run focused tests;
- run the workstream exit checks;
- update the implementation plan only when verified evidence requires a correction;
- update relevant docs and `CHANGELOG.md` with implemented behavior, not aspiration;
- report concise progress and any changed assumptions.

Non-negotiable architecture:

- Original records remain authoritative.
- Each opaque source identity normally has exactly one L1 Markdown projection identity.
- Native Markdown/plain text is not duplicated merely to satisfy a file-count rule.
- Relationships are ledger data with hashes, evidence, method, state, and invalidation—not generated
  Markdown notes.
- L2 is many sources to few purpose-specific knowledge views, ephemeral by default.
- Reviewed views become stale when dependencies change and are never silently overwritten.
- `INDEX.md` is the manual guide exception; authoritative Markdown sources and operational controls
  remain allowed when explicitly classified.
- Deterministic correctness must not depend on an AI model.
- Do not add a vector database.
- Do not create a second watcher, lifecycle authority, portal database, or parallel sync system.
- Do not re-create the old MOC/entity-page/curated-note factory under new names.

Implementation requirements:

- Start by converging all product, methodology, profile, sync, security, template, and agent
  contracts.
- Build a read-only Markdown inventory/migration report before any legacy-content write mode.
- Add L1 cardinality and allowed-Markdown lint enforcement before cleaning the Ontario example.
- Store relationship, evidence, dependency, review, L2, and context metadata through versioned
  migrations in the existing local derived-state boundary.
- Implement deterministic relationships before optional semantic proposals.
- Tie invalidation to applied journal events and reconciliation.
- Implement L2 state, pin/review, and explicit promotion to an authoritative record.
- Implement metadata-only selection manifests, dynamic saved context, and frozen evidence packs as
  distinct modes.
- Make the portal consume shared backend report/state models; JavaScript must not infer independent
  authority or semantics.
- Add unit, migration, idempotence, structural performance, prompt-safety, no-data, rights, browser,
  packaging, and end-to-end tests required by the plan.

After the implementation gates pass, perform the required post-completion product proof. Continue
using `examples/ontario-electricity-evidence-vault/` as the single canonical Ontario topic; do not
create a competing Ontario example.

For the corpus proof:

1. Research current relevant Ontario electricity documentation from official and non-official
   sources, including PDF, Word, Excel, CSV, Markdown/text, web references, presentations when
   available, and a repository or structured-code source.
2. Use only synthetic or genuinely public, permissively licensed material in the committed example,
   with exact source, licence, attribution, retrieval date, SHA-256, and disposition in
   `examples/DATA_PROVENANCE.md` and a machine-readable acquisition manifest.
3. Treat official publication and public downloadability as insufficient proof of redistribution
   rights. Use metadata-only references or an operator-controlled disposable local corpus when
   rights are unclear or files are too large for the repository.
4. Never import private GuildBuild/Data Lab material, unpublished IESO work, company/client data,
   personal information, credentials, forecasts, alerts, or proprietary analysis.
5. Target at least 200 eligible source records across at least five format classes and ten
   publishers/source series; use 500–1,000 local records when rights, storage, and runtime make that
   reasonable. The committed public subset may be smaller.
6. Use a disposable working copy of the canonical Ontario vault for destructive lifecycle tests or
   non-committable sources. Do not pollute the repository or public portal.

Run the complete user journey on that corpus:

- clean install/preflight;
- plan and full baseline sync;
- relationship build/review state;
- L2 generation and review/staleness;
- dynamic and frozen context assembly;
- status, lint, conversion, safety, and provenance checks;
- unchanged idempotent rerun;
- one-source bounded change refresh;
- move/delete/restore plus reconciliation and recovery;
- derived-state rebuild and hash/count comparison;
- local content-inclusive portal generation.

Serve the portal locally and validate it with automated browser checks and human visual review.
Exercise source/L1 lineage, typed relations and evidence anchors, proposed/accepted/rejected/
invalidated edges, generated/reviewed/stale views, dynamic/frozen context, metadata-only safety,
content-inclusive warnings, search/filtering at scale, keyboard navigation, responsive layout, long
filenames, and graph readability. Capture report, ledger, hash, browser, and screenshot evidence.
Screenshots alone are not completion proof.

Run the complete local gate before requesting review or any push. At minimum:

```bash
python3.11 -m pytest
mirrorarc --root examples/ontario-electricity-evidence-vault lint
python3.11 scripts/sync_template_copies.py --check
python3.11 scripts/no_data_scan.py
python3.11 -m build
python3.11 -m pip check
git diff --check
```

Use a disposable Python 3.11 environment and install the package/build tooling as required. Run
focused tests during development rather than repeatedly paying for the full gate.

Do not commit, push, merge, deploy, publish, contact source owners, or update GitHub Pages unless I
explicitly authorize that external action. Do not force-push or rewrite history. If later authorized
to ship, follow the repository's cz1993 authorship, independent review, local-first CI thrift, and
live merge-gate rules.

The overall goal is complete only when every final acceptance criterion in Workstream 10 passes and
the final report includes:

- changed files/modules and architectural decisions;
- exact test commands/results;
- source and rights composition;
- source/L1/L2/relationship/context counts;
- bounded invalidation and performance evidence;
- the local portal URL and passed browser scenarios;
- visual evidence paths where created;
- known limitations;
- final git status and explicit external-action status.

If an acceptance criterion cannot pass, keep making safe in-scope progress. Report a blocker only
when the same binding condition has recurred enough to meet the formal blocked rule and no safe
alternative remains.
