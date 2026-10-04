# Trustworthy Context — Post-development Review

Status: not started. Reviewer: originating planning session. Author/developer acceptance: none.

This checklist belongs to the [execution plan](TRUSTWORTHY_CONTEXT_EXECUTION_PLAN.md). It is a
local post-development review, not a request to invoke ADS, hosted CI, or another reviewer agent.
The development session supplies evidence; this planning session determines acceptance.

## Review input

- [ ] Read actual `docs/TRUSTWORTHY_CONTEXT_HANDOFF.md` once supplied; do not create passing evidence.
- [ ] Verify baseline HEAD/branch, initial dirty scope, final intended file manifest/hash/deletions,
      dependency versions, and live working-tree drift since validation.
- [ ] Separate pre-existing implementation from new changes; inspect the combined shipping scope.
- [ ] Reconcile every W0–W6 and TC-01–TC-07 item to evidence or an explicit unresolved condition.

## Independent checks

- [ ] Inspect span merge/truncation and replay a disjoint-span citation regression.
- [ ] Exercise metadata-only policy through document/code/frozen/saved-definition entry points.
- [ ] Verify the complete export's budget semantics, overhead handling, and non-ASCII behavior.
- [ ] Recheck staged/unstaged/rename/delete base semantics against the analyzed tree.
- [ ] Verify Catalog action preserves task/symbol/change selection and safely represents inputs.
- [ ] Inspect streaming output limits, timeout/process cleanup, and snapshot tamper/race handling.
- [ ] Re-run representative focused tests independently; inspect full-suite logs and exact tree.
- [ ] Check retrieval identity/deduplication, accepted-edge restrictions, stable ranking, and rebuild.
- [ ] Review benchmark raw evidence where permitted, held-out tasks, fair baselines, model/version/
      prompt/budget controls, missing runs, and unsupported-input differences. No fabricated grades.
- [ ] Review CodeGraph and Docling adoption/defer decisions and dependency/privacy impacts.
- [ ] Replay the fresh-wheel journey outside the source checkout; check no editable-install leakage.
- [ ] Inspect desktop/narrow/keyboard behavior and metadata/content distinction in passive HTML.
- [ ] Run diff/no-data/template-copy checks, inspect generated-artifact scans and original hashes.
- [ ] Verify documentation does not imply Linux/hosted/production/model-quality proof absent evidence.

## Verdict record — fill only after review

- Reviewed tree fingerprint and timestamp: pending.
- Required gates passed / failed / pending: pending.
- Findings with severity, reproduction, affected files and acceptance condition: pending.
- Benchmark outcome and permitted product claims: pending.
- Deferred experiments and rationale: pending.
- Verdict: NOT REVIEWED (later: CHANGES REQUIRED, ACCEPTED WITH EXPLICIT LIMITATIONS, or ACCEPTED).
- Approved shipping scope and fingerprint: pending.

An accepted limitation must not conceal an unresolved safety/citation/policy regression. Repeat
review after corrections against a new fingerprint; do not approve unseen changes. If material
source or dependency changes occur after final testing, rerun affected gates before acceptance.

## Shipment checkpoint

- [ ] Operator confirms the reviewed result is finalized and activates one consolidated shipment.
- [ ] Verify remote URL, owner identity (`cz1993`), live base/head and intended full change scope.
- [ ] Resolve hosted-check policy versus live branch protections without silently changing settings.
- [ ] Inspect CI/Pages/release triggers; explicitly resolve automatic deployment before pushing.
- [ ] If zero hosted runs are required, review a minimal manual-only workflow change first.
- [ ] Create one owner-authored PR containing the accepted scope and local Test Matrix, naming the
      reviewer and exact evidence fingerprint. No intermediate workstream PRs or force-push.
- [ ] Ensure PR head matches accepted/tested content; record any necessary revalidation after rebase.
- [ ] Merge only the accepted head under the owner; record PR URL and merge SHA.
- [ ] Report final Git state, shipment outcome, and whether any deployment occurred or remained off.

## Prompt to return to the planning session

> Development is ready for review. Read `docs/TRUSTWORTHY_CONTEXT_HANDOFF.md` and the execution
> plan, then independently review the current working tree using
> `docs/TRUSTWORTHY_CONTEXT_REVIEW.md`. Compare actual evidence with every acceptance criterion,
> rerun proportionate read-only/disposable checks, and give a severity-ranked verdict with any
> bounded corrections. Keep this session in review mode: do not implement fixes, commit, push,
> merge, or deploy. Identify whether the result is ready for the single final GitHub shipment.
