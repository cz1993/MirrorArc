# MirrorArc Repository Intelligence Execution Kickoff

Paste the prompt below into a new Codex session.

---

Work in `/Users/cz/workspaces/cz1993/MirrorArc`.

Create a goal first with this objective:

> Deliver MirrorArc Repository Intelligence end to end: a simple optional local code-analysis
> workflow, revision-bound governed evidence, context-pack integration, and a friendly portable
> Catalog experience that a new user can install and use with low learning effort.

Pursue the goal continuously until the final product proof in
`docs/CODE_INTELLIGENCE_EXECUTION_PLAN.md` passes or a genuine binding blocker remains. Do not stop
after another plan, adapter skeleton, schemas, mocked tests, or an unverified UI.

This project and batch do **not** use ADS or require independent review. Do not invoke the bilateral
review protocol, create a reviewer session, wait for review, or treat the absence of a PR/hosted CI
as a blocker. Do not commit, push, publish, deploy, or perform a global installation unless the
operator separately authorizes that action.

Before editing:

1. Read the applicable `AGENTS.md`, then read in this order:
   - `README.md`
   - `docs/MIRRORARC_WHITEPAPER.md`
   - `docs/PRODUCT.md`
   - `docs/CODE_INTELLIGENCE_EXECUTION_PLAN.md`
   - `docs/PRODUCT_IMPLEMENTATION_PLAN.md` only for the implemented baseline and existing gates
   - `docs/SECURITY_MODEL.md`
   - `docs/RECOVERY.md`
   - `docs/PROFILE_SCHEMA.md`
2. Inspect `git status`, current HEAD/branch, package structure, repository mirror code,
   relationship/context stores, CLI, Catalog report/UI, tests, ignore rules, and the existing
   synthetic repository fixture.
3. Preserve every existing user-owned modification. Do not reset, stash, delete, reformat, or
   overwrite unrelated work.
4. Verify current behavior before assuming a gap. Reuse the repository mirror identity, cloning,
   auth, lifecycle, relationship, context, catalog, safety, and template-copy foundations.

## Binding product direction

- Implement one provider only for the first release: CodeGraph through its ordinary local CLI.
- Use codebase-memory-mcp as a reference for coverage/confidence/root-confinement patterns only.
- Do not add vector search, bulk graph import, a provider daemon, MCP dependency, agent/editor
  configuration, a second watcher, connector, lifecycle authority, database, or sync system.
- Do not build a plugin framework, provider registry, abstract factory, generic graph-query layer,
  or future-provider compatibility surface.
- Keep CodeGraph behind one small subprocess adapter. Prefer its JSON commands. Do not make
  correctness depend on parsing human-formatted `explore` output.
- Start with the researched **CodeGraph v1.5.0** release and keep the supported version pinned.
- Resolve evidence from the exact repository revision/tree yourself. Record paths, line ranges,
  hashes, provider version, freshness, warnings, heuristics, and omissions.
- Treat the provider index as ignored, disposable local cache. Do not commit provider databases,
  cached checkouts, source bodies, or graph artifacts.
- Bulk AST nodes and edges stay outside MirrorArc's relationship ledger. Register only bounded
  analysis/context artifacts and their repository dependencies.
- Preserve original repositories as authority, repository Markdown as L1, MirrorArc's ledger as
  governed relationship state, and the Catalog as presentation only.

## User experience to deliver

The basic journey must remain approximately:

```bash
mirrorarc --root <vault> code doctor
mirrorarc --root <vault> code analyze --repo <repo-id>
mirrorarc --root <vault> catalog --html
```

Keep the CLI smaller if implementation evidence supports combining modes. Default output must use
plain product language; keep raw provider terminology under verbose/debug output. Every operational
command must support stable `--json` where the Catalog or automation needs it.

`code doctor` returns only Ready, Setup needed, or Attention, followed by the exact next action.
MirrorArc must never run `codegraph install`, modify global agent configuration, start its MCP
server, or manage a daemon. Every managed provider subprocess must set:

```text
DO_NOT_TRACK=1
CODEGRAPH_TELEMETRY=0
CODEGRAPH_NO_UPDATE_CHECK=1
```

Keep provider installation separate from the Python package. `code doctor` should show a pinned
standalone provider-install command and the retry command, but MirrorArc must not execute the
installation. Do not create a Python optional-extra shim, downloader, or package manager.
Verify the upstream installer and v1.5.0 checksums in a disposable environment before publishing
its command as the recommended setup path.

Keep the public code CLI to `code doctor`, `code analyze`, and `code status`. Put optional symbol
inspection and changed-path/base-ref analysis behind clear `code analyze` options rather than
adding more top-level commands.

The generated Catalog should add a Code view for repository artifacts with:

- current revision and freshness;
- a concise repository overview;
- inspected symbol/change result;
- exact files and line evidence;
- an ordered call path;
- direct/transitive impact and candidate affected tests;
- visible coverage, heuristic, omission, and stale-state warnings;
- an Add code evidence to context selection action.

Use cards, tables, and ordered paths with progressive disclosure. Do not default to a graph and do
not add 3D visualization. The answer, evidence, warning, and next action must be understandable
without documentation. Provide useful empty/setup/failure states with a copyable next command.
Keep keyboard access, responsive layout, long-path readability, safe rendering, and the existing
metadata-only/content-inclusive boundary.

The browser remains self-contained and passive: analysis happens before catalog generation. No
local process launch, server requirement, network fetch, or JavaScript inference is allowed. The
context action may update the existing selection manifest or present a copyable CLI command; it
must not claim that passive HTML created a governed dynamic/frozen pack.

## Execution sequence

Follow `docs/CODE_INTELLIGENCE_EXECUTION_PLAN.md`:

1. **Provider spike** — verify CodeGraph v1.5.0 and the required CLI commands against the
   existing synthetic Python repository in an isolated temporary installation. Record real output
   contracts, errors, freshness behavior, and side effects. Do not install globally.
2. **Snapshot and adapter** — implement bounded stdlib subprocess execution, revision/tree
   identity, local cache, source-span resolution, atomic valid-result publication, and staleness.
3. **CLI and governed context** — deliver the minimal commands, stable JSON, repository overview,
   symbol/call/impact/affected-test results, and revision-bound dynamic/frozen code evidence.
4. **Friendly Catalog UI** — extend the Python report model and portable UI with current, empty,
   stale, and failure states; do not infer new backend truth in JavaScript.
5. **Deployment and proof** — document the short first-run path, update applicable profile,
   security/recovery/product docs and changelog, then execute the clean-wheel product proof.

Make reasonable implementation decisions autonomously. Collapse unnecessary commands or modules.
Do not expand the scope because an external project has more features.

## Proportionate validation

Avoid both under-testing and test sprawl. During development run only focused tests for the slice
being changed. Add tests only for a user-visible promise, authority/privacy boundary, external CLI
contract, or regression-prone failure mode.

Required coverage is limited to:

- small recorded provider JSON fixtures for adapter success/error/staleness;
- one real provider smoke against the existing synthetic Python repository;
- CLI ready/setup/success/stale/failure behavior;
- revision-bound context citations, budgets, and omissions;
- three browser journeys—no analysis, current analysis, stale/failure—with narrow viewport and
  keyboard checks folded into them;
- the existing full repository gate, template-copy check, no-data scan, build, and fresh-wheel
  smoke once near completion.

Do not add a language matrix, second provider, large benchmark corpus, exhaustive parameter
permutations, duplicate snapshots, or unrelated tests.

## Final proof and finish line

Use a disposable copy and clean Python 3.11 environment. Prove all of the following:

1. install the built MirrorArc wheel and documented optional provider path;
2. `code doctor` reports Ready;
3. `code analyze` initializes/synchronizes provider state without separate provider knowledge;
4. one known symbol resolves to correct source lines and hashes;
5. one controlled change produces clearly labeled candidate affected tests;
6. a bounded context pack includes revision-bound code evidence and omissions;
7. the Catalog renders useful no-analysis, current, and stale/failure experiences at desktop and
   narrow widths with keyboard access;
8. telemetry, update checks, global configuration writes, MCP, daemons, and tracked provider state
   remain absent;
9. deleting disposable derived state permits a successful rebuild;
10. focused tests and the final existing local gates pass.

Update docs and `CHANGELOG.md` to describe only behavior that was actually proven. Do not claim
hosted, cross-platform, or production proof from local tests.

At completion, report:

- the shipped user journey and exact commands;
- files/modules changed and key decisions;
- CodeGraph version and installation method proven;
- exact focused and final test results;
- source revision/evidence/context/UI proof;
- telemetry/privacy/cache behavior;
- known limitations;
- final git status and explicit confirmation that nothing was committed, pushed, deployed, or
  published unless separately authorized.

If a provider command or deployment check fails, form one concrete hypothesis and try a bounded
fix. If the pinned provider cannot satisfy the plan's safety and output contract, report exact
evidence instead of beginning a second-provider implementation. Do not declare a blocker merely
because implementation is difficult or the first attempt failed.
