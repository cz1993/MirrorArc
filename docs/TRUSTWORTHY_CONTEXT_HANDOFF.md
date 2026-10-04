# Trustworthy Context — developer handoff

Date: 2026-09-19. Developer: Codex. Owner: cz1993.
Status: implementation and local evidence supplied; **NOT REVIEWED, NOT ACCEPTED, NOT SHIPPED**.
The originating planning session owns [review](TRUSTWORTHY_CONTEXT_REVIEW.md). No acceptance box
has been checked by the developer. The active [execution plan](TRUSTWORTHY_CONTEXT_EXECUTION_PLAN.md)
remains the scope contract; older plans are historical baseline only.

## Baseline and scope

Work used the existing dirty checkout `/Users/cz/workspaces/cz1993/MirrorArc` directly.
Branch `codex/knowledge-projection`, HEAD `15ce475a5077ce9d048a3f38a9a832a08976ffd9`.
Initial status, full diff, tool versions and per-file SHA-256 inventory are retained
at `/var/folders/nf/bttgh08105s1k2b70m_gf04c0000gn/T/mirrorarc-trustworthy-dii2bgio`.
That directory predates changes in this session. HEAD alone does not identify this work.

Final intended shipping files, including pre-existing dirty work, new untracked files and explicit
deletions: [TRUSTWORTHY_CONTEXT_FILES.json](TRUSTWORTHY_CONTEXT_FILES.json).
Manifest digest and full-tree fingerprint: manifest SHA-256 `de6eb32f612d5219e9a1e2a53fa8313194b337174f670fda8361d18ae22a2079`; full-tree SHA-256
`15a37c5dc4f978ef5db77a1bfaeb44ff54e04533cac14d42513546d790f512e0`.
The manifest excludes itself and this handoff to avoid self-referential hashing. All other
tracked/nonignored untracked regular files contribute to its full-tree fingerprint; ignored
validation caches are not shipping files. Its per-path baseline classification distinguishes
preserved prior implementation from overlapping edits and new additions. Do not stage only this
session's edits: the required implementation began in an extensive dirty tree.

## Workstream outcome

| Workstream | Developer result | Evidence / limits |
| --- | --- | --- |
| W0 | complete | Dirty baseline and isolated environment captured; initial focused suite 14 passed, 1 optional-provider skip in 16.17 s. |
| W1 | implemented and locally checked | Exact spans/hashes, current policy enforcement, final export budgets, dirty-base semantics, preserved Catalog requests, streaming limits, verified snapshots; regressions below. |
| W2 | deterministic benchmark complete; model evaluation pending | Fixed 12-task pack before tuning; baseline and held-out results retained; no endpoint approval or invented grades. |
| W3 | implemented, opt-in | FTS5/BM25 in existing state.sqlite; current hashes, stable identity/ranking, accepted/current one-hop expansion, bounded candidates and rebuilds. Full sync/query refresh use the existing invalidator. |
| W4 | implemented and browser checked | Task → evidence → warnings → export, saved commands and current frozen status, passive metadata/content distinction; desktop/narrow/keyboard evidence below. Independent novice feedback remains pending. |
| W5 | bounded experiments complete | Retain CodeGraph 1.5.0 and MarkItDown 0.1.7; no Docling/PageIndex integration. |
| W6 | local proof and handoff supplied | Final gate, wheel, synthetic originals, browser and manifest evidence; independent planning acceptance remains pending. |

No vector database, second watcher/lifecycle/store authority, provider framework, daemon, cloud
service, MCP dependency, global configuration change or globally installed package was introduced.

## Integrity regressions and implementation

`tests/test_trustworthy_context.py` exercises public CLI/context boundaries with synthetic vaults;
existing package tests still run. Focused coverage maps to the original findings:

| Finding | Correction and evidence |
| --- | --- |
| TC-01 | `service.py` unions exact numbered source lines, preserves disjoint ranges, verifies file hashes, recomputes excerpt hashes and trims complete lines. Tests compare every reported range with original source text, including overlap/disjoint cases. Document exports record exact Unicode character offsets and verified L1 generated-region/source hashes. |
| TC-02 | Current profile modes checked before rejected paths can create state or invoke providers, including saved definitions and code context. Tests verify metadata-only denials and byte-identical state after revocation. |
| TC-03 | Shared export code bounds the complete serialized UTF-8 JSON envelope, including instructions/citations/omissions. `max_tokens` is a compatibility estimate at four bytes per estimated token; overhead-only overflow fails. Tests cover Unicode, tiny budgets, dropped items, code metadata and task-sensitive identities. Transport wrapper JSON is not the exported envelope. |
| TC-04 | Base resolves safely, then base-to-current-working-tree diff plus nonignored untracked files uses NUL-separated names. Staged/unstaged/rename/delete changes are preserved. Deleted/missing/binary/excluded evidence is omitted rather than cited as current text. The fixed snapshot exclusions remain explicit in the security contract. |
| TC-05 | Shell-quoted Catalog actions retain symbol/base/explicit changed paths and saved definitions, including spaces and option-like input. Reference-only HTML never claims included source bodies. |
| TC-06 | Provider pipes are capped while streaming; monotonic timeout and process-group cleanup apply on this POSIX host. stdout/stderr overflow and hung-provider regressions pass. No Windows process-cleanup claim. |
| TC-07 | Bounded snapshot traversal and post-copy/reuse/post-provider identity verification reject tampering and controlled copy races while retaining the previous valid analysis. Real provider cache loss/rebuild is exercised twice. |

Additional public regressions verify first-use query refresh, source edit/delete and disposable
FTS cache rebuild, proposed/rejected edge exclusion, full-sync opaque-source invalidation,
immutable frozen bytes, and Catalog code-pack staleness from the existing public status path.

Retrieval is lexical/heading-based, bounded to 500 eligible candidates, 256 KiB per file,
8 MiB indexed text, 10,000 chunks of 40 lines and 32 query terms. It indexes allowed current
native text or verified L1, deduplicates source identity, uses stable score/identity/span ties,
and expands one permitted accepted/hash-current hop. Cache schema is versioned/disposable.
FTS5 absence gives a clear query error; existing no-query lenses remain available. The private
index contains derived text and belongs under the existing local state privacy boundary.

## Validation evidence

Host: macOS arm64; Python 3.11.15. Editable development environment:
`/tmp/mirrorarc-tc-venv`. Fresh wheel runtime:
`/tmp/mirrorarc-tc-final/runtime`. Tested dependencies:
[constraints](TRUSTWORTHY_CONTEXT_CONSTRAINTS.txt). This is an observed test environment,
not a cross-platform lock. `pip check` reports no broken requirements.

Final full suite: **570 passed, 0 failures, 0 skips, 223.20 seconds; process exit 0**.
Log: `/tmp/mirrorarc-tc-final/full-tests-complete.log`.
Earlier clean full runs: 565 passed / 239.18 s; 567 passed / 234.17 s; 569 passed / 228.54 s;
569 passed / 224.58 s. Later runs were justified by first-use/full-sync/export or browser-found
corrections, not re-running hosted CI. These historical counts are not the final-tree count.

Some earlier combined focused invocations printed passing tests and then exited 134 with a native
`libc++` recursive-mutex failure. One bounded isolation check (plain imports and separate focused
runs) did not reproduce it; no cause or fix is claimed. Final full runs exited cleanly. Logs remain
outside the tree; retain this limitation if it recurs on another host.

Final static gate: `/tmp/mirrorarc-tc-final/static-gate.json` and named logs. All checks return 0:
`git diff --check`, repository no-data scan, template-copy consistency, dependency consistency,
compilation of all applicable Python files, six POSIX shell syntax checks and a separate scan of
generated HTML, L1 and context JSON. No safeguards were weakened. Early strict no-data failures
identified generated build/pytest/bytecode/egg-info residue; it was moved to
`/tmp/mirrorarc-tc-final/retained-build-test-residue` with a movement record, not deleted.

Template and regenerated disposable Ontario lints use the installed runtime through each vault's
`tools/lint_vault.py`. Both return 0, all warning/error categories zero. Ontario inventory:
59 sources, three opaque sources, three L1, two reviewed L2, zero stale L2/unexplained Markdown.
Plan/sync/status/lint logs are `/tmp/mirrorarc-tc-final/ontario-*.log`; template log is
`template-lint-final.log`. The original example was not regenerated in place. All **28** baseline
example original/fixture files match their initial hashes (`repository-originals.json`).
Disposable Ontario original hashes and fresh-wheel journey hashes were also checked before the
intentional synthetic mutations.

Wheel: `/tmp/mirrorarc-tc-final/wheels/mirrorarc-0.1.0a1-py3-none-any.whl`.
SHA-256: `79cd0b04c68a0e3c678ba74dca56206a60c893e0034b0987025b70ec43efaa66`. Built from a disposable copy of the complete dirty source;
build outputs never needed to enter the checkout. Runtime imports resolve to
`/private/tmp/mirrorarc-tc-final/runtime/lib/python3.11/site-packages/mirrorarc/__init__.py`,
not the editable checkout. Packaged source files match the final checkout byte-for-byte
(`wheel-source-match.json`). The final wheel journey is `/tmp/mirrorarc-tc-final/journey6`:
21 CLI commands, exact excerpts, allowed context, source mutation → stale state, immutable prior
frozen bytes, revised context, failed provider preserving prior evidence and two equivalent
CodeGraph cache rebuilds. `commands.json` records every command/exit/log; `journey.json` records
source hashes, context IDs and matching rebuilt analysis hash.

Reproduce from a new isolated environment after installing the wheel and dependencies:

```sh
# Run outside the checkout. Use a new output directory each time.
/tmp/mirrorarc-tc-final/runtime/bin/python /Users/cz/workspaces/cz1993/MirrorArc/scripts/validate_trustworthy_context.py \
  --repo /Users/cz/workspaces/cz1993/MirrorArc \
  --output /tmp/mirrorarc-tc-review-journey \
  --codegraph /tmp/mirrorarc-tc-upstream/codegraph-1.5.0-offline
```

Full-suite reproduction from the checkout (local only):

```sh
PYTHONPYCACHEPREFIX=/tmp/mirrorarc-review-pycache \
MIRRORARC_CODEGRAPH_SMOKE=/tmp/mirrorarc-tc-upstream/codegraph-1.5.0-offline \
/tmp/mirrorarc-tc-venv/bin/python -m pytest -o cache_dir=/tmp/mirrorarc-review-pytest-cache
```

## Benchmark and provider decisions

[Per-task results](TRUSTWORTHY_CONTEXT_RESULTS.md): ten evidence-bearing tasks average expected-source
coverage 0.55 → 0.90; three held-out tasks 0.50 → 0.67. `tc11` regresses 1.0 → 0.0. Both
insufficient-evidence tasks become empty selections. Neither result measures model answers,
semantic citation accuracy, abstention, privacy/prompt resistance or corrections. Model metrics
remain null; three stochastic repeats have not run. Same-task source/prompt/budget controls and
unsupported code-wrapper/opaque-extraction differences are documented. No general superiority claim.

[Upstream experiment record](TRUSTWORTHY_CONTEXT_EXPERIMENTS.md) and `/tmp/mirrorarc-tc-upstream`:
CodeGraph 1.5.0/1.6.0 both pass the small actual-binary contract comparison; no concrete 1.6 benefit
was shown. Retain 1.5.0. Docling 2.129.0 lacks offline RapidOCR assets; one OCR-disabled retry
still requires a layout model. No download/adoption. MarkItDown recovered table values,
interleaved columns and produced no scan text. Neither experiment provided page anchors.
PageIndex was not run/integrated; Promptfoo not added. Package/binary acquisition used network;
extraction/provider experiments ran with OS network denial. No paid model call or private-data
transmission occurred.

## Browser evidence

Portable final HTML is in `journey6`: `empty.html`, `current.html`, `metadata.html`, `stale.html`,
`failure.html`. Generated by the installed wheel. Browser was served on loopback only because the
browser tool rejected file URLs; the HTML itself has no server dependency. Browser walkthrough
used the Playwright CLI skill, Chromium, 1440×900 and 390×844. No page console warnings/errors or
resource fetches were observed. `window.syntheticInjection` remained undefined when the literal
script-bearing synthetic source was rendered. No remote link or open-file link was followed.

Screenshots: `/tmp/mirrorarc-tc-final/*-final.png`. Authoritative final-state capture list and
checks: `/tmp/mirrorarc-tc-final/browser-proof.json`. The empty panel explains setup; current code
shows exact ranges and included bodies; metadata panel says reference-only without function text;
stale/failure states retain previous evidence with visible status. The dialog preserves task
resolve/freeze commands. Narrow commands wrap without modal/page horizontal overflow. Shift-Tab/
Tab cycle within the dialog; Escape restores opener focus. Source long paths wrap; narrow code
tables remain dense and use contained excerpt scrolling. This is an agent walkthrough, not a
novice usability study. Operator feedback belongs in planning review.

Reproduce by serving the journey directory on a free loopback port, opening each HTML in Chromium,
selecting `local/pipeline` → `Code evidence`, and opening `Build context pack`. At narrow width,
open `Browse` first. For staleness inspect `Frozen evidence · stale` in the dialog. Repeat at both
sizes, test keyboard focus and compare metadata/content output. Close only the server/browser
created for this check; unrelated local services were not stopped.

## Remaining authority, limitations and shipment

- Empirical model evaluation needs explicit endpoint/model/version, permitted-data and spend
  approval, plus an approved runner and human grading. No endpoint is silently selected; the
  deterministic rerun commands are ready. This condition is not a fabricated model pass.
- Independent planning review/acceptance and novice/operator feedback are pending.
- No local Linux runtime/container was available. No Linux, hosted, production or deployment
  proof is claimed. Native dependency shutdown flakiness from earlier focused runs remains noted.
- Small synthetic coverage is not universal repository/language/extractor quality. CodeGraph
  affected tests are candidates; the fixed snapshot exclusions and resource limits apply.
- Final Git state: 107 modified tracked files, 6 deleted tracked paths, 65 untracked files;
  no staged files. The six deletions were already present in the baseline. Full individual-path
  status: `/tmp/mirrorarc-tc-final/final-git-status.txt`. Nothing was committed, pushed, merged, tagged,
  published, deployed or globally installed. No remote settings or global agent configuration
  were changed. No reviewer or development subagent was spawned.
- CI/Pages/release triggers were inspected, not dispatched or edited for this session. CI runs on
  PRs/main pushes; Pages auto-deploys on matching main-path pushes (including source/example
  changes); release runs on `v*` tags. **Code shipment could trigger Pages.** The owner/planning
  shipment checkpoint must explicitly resolve that before any push/merge. Remote protections
  were not changed or claimed verified.

Preserve the external evidence directories before temporary-directory cleanup. Planning review
must compare the live tree with the manifest, rerun proportionate checks and record its own
verdict. Only after that and the operator's final shipment checkpoint may the one consolidated
owner-authored PR/merge occur.
