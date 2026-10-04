# MirrorArc Repository Intelligence Execution Plan

**Status:** implemented and locally proven

**Date:** 2026-08-12

**Research inputs:**

- [`DeusData/codebase-memory-mcp`](https://github.com/DeusData/codebase-memory-mcp)
- [`colbymchenry/codegraph`](https://github.com/colbymchenry/codegraph)

**Execution prompt:**
[`prompts/CODE_INTELLIGENCE_EXECUTION_KICKOFF.md`](prompts/CODE_INTELLIGENCE_EXECUTION_KICKOFF.md)

**Repository:** `/Users/cz/workspaces/cz1993/MirrorArc`

## 1. Outcome

Deliver an optional **Repository Intelligence** capability that lets a normal MirrorArc user:

1. connect or select a governed source repository;
2. run one understandable analysis command;
3. inspect architecture, relevant symbols, call relationships, change impact, affected tests,
   freshness, and exact source evidence in the Catalog Explorer;
4. add bounded, source-backed code evidence to a MirrorArc context pack.

The feature must preserve MirrorArc's product identity. It is not a general code-search product and
does not replace the existing repository mirror, relationship ledger, lifecycle engine, context
assembly, or catalog. It adds a disposable structural read model beneath those governed surfaces.

Success means a new user can reach a useful repository result with one short setup path, one
analysis command, and no knowledge of MCP, Cypher, SQLite, ASTs, or provider terminology.

## 2. Product Decision

### First implementation provider

Use **CodeGraph** as the single optional engine for the first release, through its local CLI and
machine-readable commands. It aligns with MirrorArc's no-vector-database direction, exposes
symbol/call/impact/affected-test operations, keeps its index in local SQLite, and provides useful
references for task-shaped output, freshness warnings, progressive disclosure, and output budgets.
The implementation spike starts with the currently researched release, **CodeGraph v1.5.0**. Pin
the version in documentation and product evidence; do not resolve a floating latest release during
normal MirrorArc operation.

Use `codebase-memory-mcp` as a design and benchmarking reference only in this slice. Its index
coverage checks, tiered confidence language, explicit root confinement, and one-shot CLI operation
are valuable patterns. Do not integrate its vector-backed semantic query, ADR store, daemon,
watcher, shared graph artifact, or agent-configuration installer.

Do not build a multi-provider framework in this release. Keep the CodeGraph subprocess boundary
small enough to replace later, but do not add provider registries, plugin discovery, abstract
factories, or compatibility layers without a second proven provider requirement.

### Supported CodeGraph surface

Prefer stable JSON output from:

```text
codegraph status --json
codegraph query ... --json
codegraph callers ... --json
codegraph callees ... --json
codegraph impact ... --json
codegraph affected ... --json
codegraph files ... --json
```

Do not make correctness depend on parsing human-formatted `codegraph explore` output. MirrorArc
should read any included source span itself from the pinned repository snapshot, then record the
path, line range, file hash, repository revision, and truncation state.

### Authority boundary

- The repository and its recorded revision remain L0 authority.
- The existing repository Markdown mirror remains the L1 reading surface.
- The CodeGraph database is local, disposable provider cache—not MirrorArc authority.
- Provider nodes and edges are not bulk-imported into MirrorArc's relationship ledger.
- Only bounded results selected for a report or context pack become MirrorArc derived artifacts.
- Heuristic or unresolved provider relationships are visibly labeled and never silently promoted.
- A commit/tree mismatch makes previous analysis stale; it never remains silently current.

## 3. User Experience Contract

### First-run flow

The intended path is:

```bash
mirrorarc --root <vault> code doctor
mirrorarc --root <vault> code analyze --repo <repo-id>
mirrorarc --root <vault> catalog --html
```

`code doctor` must give one clear verdict:

- **Ready** — provider found, compatible, telemetry disabled, repository resolvable;
- **Setup needed** — show one recommended install command and a retry command;
- **Attention** — explain the exact version, path, repository, permission, or stale-index problem.

Keep provider installation separate from the Python package. For macOS and Linux, `code doctor`
should recommend the provider's standalone, self-contained installation pinned to the supported
version, followed by the retry command. Do not create a Python optional extra for a non-Python
runtime, build a downloader, or silently install software. Document the command and let the user
choose whether to run it.

The researched starting command is:

```bash
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/v1.5.0/install.sh \
  | CODEGRAPH_VERSION=v1.5.0 sh
mirrorarc --root <vault> code doctor
```

Before publishing that command, the implementation session must verify the script and v1.5.0
checksums in a disposable environment and confirm that this installer only places the standalone
CLI; it must not call the separate agent-configuration command.

MirrorArc must invoke ordinary CodeGraph project commands directly. It must not run
`codegraph install`, modify global agent configuration, enable its MCP server, or start a daemon.
Set `DO_NOT_TRACK=1`, `CODEGRAPH_TELEMETRY=0`, and `CODEGRAPH_NO_UPDATE_CHECK=1` for every managed
subprocess.

### Primary actions

Keep the first-release public CLI to three actions:

- `code doctor` — readiness and actionable setup;
- `code analyze --repo <id>` — repository overview and current snapshot, with optional
  `--symbol <name>`, `--base <ref>`, or changed-path inputs for focused evidence and candidate
  affected tests;
- `code status [--repo <id>]` — current/stale/failed analysis state.

Human output should be short and action-oriented. Every command also provides `--json` for the
catalog and automation. Provider command names, database paths, and raw payloads belong under a
verbose/debug option, not in the default experience.

### Catalog Explorer

Add a **Code** view only when the selected artifact is a repository or repository projection. Its
default state should be a readable evidence dashboard, not a force graph:

- repository revision and freshness;
- languages, files, and key entry points;
- the latest inspected symbol or change set;
- relevant files and exact line anchors;
- call flow as an ordered list or compact path;
- impact grouped by direct, transitive, and test candidates;
- coverage, heuristic, omission, and staleness warnings;
- “Add code evidence to context” selection action.

Use progressive disclosure. Show the answer and evidence first; place raw provider diagnostics and
large relationship lists behind details controls. Empty and error states must say what happened and
offer an exact next command. Preserve keyboard access, responsive layout, safe rendering, long-path
readability, and the existing metadata-only/content-inclusive boundary.

The Catalog remains a generated, self-contained HTML artifact. Analysis occurs before generation;
the browser must not launch local processes, require a server, or become a second database. Its
context action may add evidence to the existing client-side selection manifest or show a copyable
CLI command; it must not pretend that a passive HTML file created a governed dynamic/frozen pack.

## 4. Minimal Data Contract

Store current analysis under the existing disposable local boundary, for example:

```text
.mirrorarc/cache/code-intelligence/<repo-id>/<revision>/
```

The exact path may change, but no provider database or source checkout is committed. Add ignore and
no-data coverage if current rules do not already protect this boundary.

One normalized analysis record needs only:

```text
analysis_id
repo_id
configured_repo
resolved_revision
local_tree_hash when applicable
provider_name
provider_version
analysis_kind
request
created_at
freshness_state
files[]: path, hash, language, selected line ranges
symbols[]: stable provider identity, kind, name, qualified name, path, range
relationships[]: source, target, kind, provenance, depth
affected_tests[]
warnings[]
omissions[]
```

Use deterministic IDs and canonical JSON ordering. Apply existing context file/token/excerpt
ceilings. Do not copy an entire repository, provider database, or unbounded provider response into
the ledger, a Markdown mirror, the catalog, or a frozen pack.

## 5. Workstream 0 — Bounded Provider Spike

### Build

- Pin and record the tested CodeGraph version; do not use a floating latest version at runtime.
- Use an isolated temporary installation or executable, never the global interactive installer.
- Run `init`, `status --json`, `query --json`, `callers --json`, `callees --json`, `impact --json`,
  `affected --json`, and `files --json` against the existing synthetic repository fixture.
- Record actual schemas, exit codes, stderr behavior, index paths, offline behavior, and stale-index
  behavior in focused adapter fixtures or tests.
- Confirm every managed invocation disables telemetry and update checks.
- Confirm the pinned standalone install path works in a clean temporary location without invoking
  `codegraph install` or writing agent configuration.

### Exit

- The selected version works on Python repositories on the current macOS environment.
- The commands needed for the MVP have bounded, parseable output.
- No agent configuration, MCP entry, watcher, daemon, telemetry event, or tracked repository file
  is created.
- If these conditions fail, stop the provider integration with exact evidence and a bounded
  recommendation. Do not start a second-provider implementation in this batch.

## 6. Workstream 1 — Snapshot and Adapter

### Build

- Add a small stdlib subprocess adapter with explicit timeouts, environment, output ceilings,
  version checks, error mapping, and JSON validation.
- Resolve a configured repository to one immutable revision. Reuse the current repository sync
  identity and cloning/auth rules rather than creating a second connector.
- For a local dirty repository, record both HEAD and a deterministic local-tree hash; clearly label
  the analysis `local-uncommitted`.
- Keep provider indexes and any temporary checkout under ignored local state. Use locks or atomic
  publication only where concurrent writes can corrupt that state.
- Normalize the small data contract above and derive source excerpts directly from the resolved
  snapshot with path/symlink/boundary validation.
- Mark analysis stale when the repository revision/tree hash no longer matches.

### Exit

- Re-running the same request against the same snapshot produces the same normalized content apart
  from declared timestamps/runtime diagnostics.
- Changing the snapshot invalidates the previous result without rewriting it as current.
- A provider failure leaves repository mirrors, manifests, and prior valid analysis untouched.
- No provider-specific schema leaks beyond the adapter module and its fixtures.

## 7. Workstream 2 — CLI and Governed Context

### Build

- Implement the minimal CLI selected in Section 3 with helpful defaults and `--json`.
- Let `analyze` initialize or incrementally sync the disposable provider index as needed; users
  should not learn separate provider lifecycle commands.
- Generate concise repository overview, symbol evidence, and affected-test reports.
- Register only the bounded analysis artifact and its repository dependency in MirrorArc state.
- Allow selected code evidence to enter dynamic or frozen context using the existing context
  budget, citation, hash, sensitivity, omission, and untrusted-content rules.
- Never treat affected tests as proof that other tests are unnecessary. Label them candidates and
  keep the repository's normal test gate authoritative.

### Exit

- A first-time user can move from `code doctor` to a useful result without provider vocabulary.
- JSON output is stable enough for the Catalog report model.
- Every displayed or exported excerpt resolves to a path/range/hash at the recorded revision.
- Context output remains within declared budgets and reports every omission.

## 8. Workstream 3 — Friendly Catalog UI

### Build

- Extend the shared Python catalog report; do not add inference logic in JavaScript.
- Add repository-level readiness, freshness, overview, inspection, impact, and warning states.
- Provide useful empty states and copyable commands when analysis is unavailable or stale.
- Use compact cards, tables, and ordered paths. Add graph visualization only if usability evidence
  shows that a particular relationship cannot be understood more clearly as a path or table.
- Add “Add code evidence to context” as a selection-manifest action or copyable governed-context
  command using the existing pack interaction and safety language.
- Keep the HTML portable and metadata-only by default. Content-inclusive mode may include only the
  bounded code excerpts already selected by the backend.

### Exit

- A new user can identify the repository, its revision, the main result, evidence, warnings, and
  next action without reading documentation.
- Desktop and narrow/mobile layouts have no clipped paths, unreachable actions, or horizontal page
  scrolling.
- Keyboard users can reach the Code view, evidence rows, details, and context action.
- The browser performs no local execution, network fetch, or independent relationship inference.

## 9. Workstream 4 — Deployment, Documentation, and Product Proof

### Build

- Add a short quickstart with the three-command first-run flow and one troubleshooting table.
- Update the `software-project` profile guidance without changing the other profiles' normal flow.
- Document local cache location, deletion/rebuild, privacy, telemetry suppression, supported
  provider version, and the fact that code results are derived and revision-bound.
- Add one synthetic repository walkthrough to the existing Ontario example rather than creating a
  second demo vault.
- Update `README.md`, relevant product/security/recovery docs, template copies when applicable, and
  `CHANGELOG.md` after behavior exists.

### Proportionate validation

Use focused tests while implementing. The intended test budget is:

- adapter contract/error/staleness tests using small recorded JSON fixtures;
- one real provider smoke test against the existing synthetic Python repository fixture;
- CLI tests for ready, setup-needed, success, stale, and provider-failure outcomes;
- context tests for revision-bound citations, budgets, and omissions;
- three browser journeys: no analysis, current analysis, and stale/failed analysis, with one narrow
  viewport pass and keyboard checks folded into those journeys;
- one final existing repository gate, template-copy check, no-data scan, build, and fresh-wheel
  smoke test.

Do not add a large language matrix, multiple providers, performance lab, duplicate UI snapshots,
or exhaustive permutations in this slice. A test must protect a user-visible promise, authority or
privacy boundary, external CLI contract, or regression-prone failure mode.

### Final product proof

From a clean temporary Python 3.11 environment and disposable copy of the existing example:

1. install the built wheel and the documented optional provider path;
2. run `code doctor` and receive `Ready`;
3. analyze the synthetic repository without separate provider commands;
4. inspect one known symbol and resolve its cited source lines;
5. identify affected tests for one controlled change;
6. build a bounded context pack containing code evidence;
7. generate and open the Catalog Explorer;
8. verify the no-analysis, current, and stale/failure UI states;
9. remove disposable derived state and prove the feature can rebuild;
10. run the final local repository and no-data gates once.

## 10. Explicit Non-Goals

- no vector embeddings or vector database;
- no bulk AST graph import into MirrorArc's ledger;
- no second watcher, repository connector, lifecycle authority, portal database, or sync system;
- no MCP-server requirement for MirrorArc users;
- no agent/editor configuration mutation;
- no provider daemon managed by MirrorArc;
- no committed `.codegraph/`, `.codebase-memory/`, provider SQLite, source checkout, or code body;
- no natural-language-to-Cypher or generic graph-query UI;
- no 3D graph or graph-first navigation requirement;
- no multi-provider framework in the first release;
- no Python optional-extra shim for installing the external provider;
- no hosted repository analysis service, SaaS, authentication system, or collaboration layer;
- no autonomous test selection, code modification, ADR creation, or promotion into authority;
- no new demo vault, large corpus acquisition, or unrelated knowledge-projection redesign.

## 11. Execution and Stop Rules

- Preserve the current dirty worktree and build on the existing knowledge-projection baseline.
- Work in the order above, but collapse modules or commands when that produces a simpler product.
- Keep one implementation workstream in progress at a time.
- Run focused checks after each coherent slice and the full existing gate once near completion.
- Do not pause for ADS, bilateral CLI review, an independent reviewer, a PR, or hosted CI. They are
  not required for this project/batch.
- Do not commit, push, publish, deploy, or install globally unless the operator separately
  authorizes that external or machine-wide action.
- Stop only for a genuine authority, destructive-data, privacy, licensing, or irreducible product
  decision. A hard implementation problem is not itself a blocker.

## 12. Completion Report

The goal is complete when the final product proof passes and the report includes:

- the shipped user journey and exact commands;
- files and modules changed;
- provider/version and deployment method proven;
- exact focused and final test results;
- repository revision, code evidence, context, and UI proof;
- privacy/telemetry/cache behavior verified;
- remaining limitations stated plainly;
- final git status and whether anything was committed, pushed, deployed, or published.

## 13. Completion Evidence

Repository Intelligence is implemented as an optional local workflow with the intended user path:

```bash
mirrorarc --root <vault> code doctor
mirrorarc --root <vault> code analyze --repo <repo-id>
mirrorarc --root <vault> catalog --html
```

The implementation uses CodeGraph v1.5.0 through ordinary bounded CLI subprocesses. The standalone
installer was downloaded and run in an isolated temporary home and install directory. The verified
installer SHA-256 was
`f4e90c6e0c1d2ac95a43fa6e82e4caf76fabdb18310afc72597314b58632e56c`; the Darwin arm64 bundle
SHA-256 was `cf5ee435a6e44d097b2f98f2b7b8b9422bb1094844404efed82519c5da1af2cf`. The installed
binary reported `1.5.0`. No global installation, agent configuration, MCP setup, daemon, deployment,
or publication was performed.

The adapter, snapshot/cache service, governed context integration, CLI, Catalog report, and portable
Code view are implemented under `src/mirrorarc/`. Recorded v1.5.0 JSON contracts and focused tests
live under `tests/fixtures/codegraph_v1_5_0/` and `tests/test_code_intelligence.py`. README,
quickstart, product, profile-schema, security, recovery, software-project profile, ignore rules,
no-data enforcement, and changelog guidance are updated.

Clean-wheel proof used a fresh Python 3.11 build environment, a separate runtime environment, and a
disposable copy of the Ontario example. `pip check` reported no broken requirements. `code doctor`
returned `Ready` with all managed subprocess privacy variables set. The known `demand_change` symbol
resolved to `src/grid_evidence/summary.py:8-11`; `tests/test_summary.py` was reported as a medium-
confidence `symbol-impact` candidate, while the normal test gate remained authoritative. Analysis
`code_analysis_c33d269bdd50e489c1ae40a0ec61` produced frozen context
`context_6395658f0ebf78a40464990f99b4`. Every cited path, line range, and file hash was checked
against the disposable source tree.

A controlled source edit changed the local revision and produced a distinct analysis identity,
while retaining the prior result and marking its frozen context stale. A forced provider failure
returned exit status 1 and retained the prior valid evidence with visible `failed` state. Moving the
entire disposable code-intelligence cache outside the vault produced `no-analysis`; two independent
rebuilds then reproduced analysis `code_analysis_9749672969a3d740aee0cbe4d7cc` and content hash
`750b1a39386afa1bac75e4d9c100c93c23fb2298fcd49ae188cdb8672fe78789` exactly.

Browser proof used the installed wheel's generated HTML, not a development-only UI. The no-analysis,
current, stale, and failed states all showed their reason and next action. Current evidence showed
the revision, languages, files, exact paths/lines/hashes, ordered call path, impact, affected-test
candidate, warnings, and context action. Only the latest analysis appeared in the browse graph after
historical reanalysis. A 390 by 844 viewport remained usable; keyboard navigation reached and
activated the code-context selection, changing its count from zero to one. All browser journeys had
zero console errors or warnings. The HTML application initiated no local process or secondary
network fetch.

Privacy and recovery checks confirmed that provider indexes exist only beneath
`.mirrorarc/cache/code-intelligence/`, never in the governed source repository; default Catalog HTML
omits code bodies; `--include-content` includes only bounded selected excerpts; provider environment
variables disable telemetry and update checks; and the isolated provider home contains no agent
configuration. Ignore rules and the no-data scanner reject tracked or staged `.codegraph/` state.

Final local validation on 2026-08-12:

- focused repository-intelligence/context/privacy suite with real provider smoke: 58 passed;
- complete repository suite with real provider smoke: 552 passed in 241.26 seconds;
- template-copy drift check: clean;
- no-data scan: OK;
- canonical template lint: OK, including zero unresolved links, orphans, or overlaps;
- Python compilation and shell syntax checks: passed;
- fresh wheel build, install, dependency check, workflow, rebuild, and browser proof: passed.

Known limitations are intentional first-release boundaries: Python is the proven language path;
affected tests are candidates rather than test-selection authority; local dirty repositories are
bound to a deterministic local-tree hash rather than a commit; CodeGraph v1.5.0 is the only
supported provider; and analysis remains an explicitly invoked, disposable local read model rather
than a watcher, daemon, MCP service, vector store, hosted service, or browser-side engine.
