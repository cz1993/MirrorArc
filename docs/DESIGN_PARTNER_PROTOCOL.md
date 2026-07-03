# Design Partner Protocol

## Purpose

Vaultwright is not validated until external operators use it on real client-shaped corpora. This
protocol keeps validation concrete, comparable, and honest.

Use `docs/DESIGN_PARTNER_RECRUITING.md` to recruit and pre-screen partners before scheduling a
run. Use `docs/PILOT_WORKSHEET.md` as the working artifact for each accepted pilot. Attach
aggregate output from `vaultwright --root "$VW" pilot --json` to the private pilot record, not to
this public repository.

Stage 3 is not complete until at least one permission-cleared external corpus runs through this
protocol. Public examples, synthetic dogfood runs, and generated benchmark corpora are engineering
evidence; they are not design-partner proof.
The stop and pivot rules for weak benchmark or self-service evidence are in
[`docs/VALIDATION_GATE.md`](VALIDATION_GATE.md).

## Target Participants

Recruit small consulting, advisory, implementation, compliance, or operations teams that handle
document-heavy onboarding or review work. Avoid broad consumer testing until this wedge is proven.
Pre-screen for authority to copy the corpus, a bounded workflow, and willingness to attempt the
second sync without hands-on help.

## Corpus Requirements

Each pilot should use a copied, permission-cleared corpus:

- 50 to 2,000 source files;
- mixed Office files, PDFs, markdown/text, spreadsheets, decks, and optional repositories;
- no files the participant is unwilling to process locally;
- no secrets committed to Git;
- one engagement or protected boundary per vault.

Set the copied pilot vault path once for the run:

```bash
export VW="/path/to/copied-pilot-vault"
```

Use the installed `vaultwright --root "$VW"` command for pilot runs. The vault-local
`python3.11 tools/vaultwright.py ...` wrappers remain compatibility fallbacks when the package is
not installed.

## Evaluation Steps

1. Baseline interview: current process, pain points, tools, security constraints.
2. Copied-vault preflight: run `vaultwright --root "$VW" sandbox --source-root <original-root>`.
3. Non-destructive inventory: run `vaultwright --root "$VW" doctor`, `plan`, and `status`.
4. First sync: run `vaultwright --root "$VW" sync --json` and capture manifests/audit logs.
5. Conversion review: run `vaultwright --root "$VW" conversion --guide` and spot-check high/medium-priority
   mirrors before relying on generated content.
6. Review exceptions: unsupported, stale, missing, unreachable, conflicted, or manual-modification
   states.
7. Catalog review: run `vaultwright --root "$VW" catalog`, `catalog --html`, and `m365` if the
   participant expects Microsoft 365 handoff.
8. Record artifact review decisions with `vaultwright --root "$VW" review` after spot-checking
   selected mirrors, catalogs, and handoff reports.
9. Curate the first hubs and entity pages.
10. Answer a fixed set of operational questions with citations.
11. Score the agent-readiness task pack across raw-folder, plain-dump, and Vaultwright-Markdown
   modes, then validate the private result pack with `--require-results`, `--require-citations`,
   and `--require-prompt-safety`.
12. Capture aggregate evidence: run `vaultwright --root "$VW" pilot --json` and
   `vaultwright --root "$VW" pilot --worksheet`, then store the outputs with the private pilot
   worksheet.
13. Modify or move selected sources, have the participant rerun sync without help, then verify
   lifecycle reporting and unexpected regressions.
14. One-week follow-up: determine whether the participant returned to the vault.

## Required Metrics

Record:

- source file count and total size;
- supported, unsupported, skipped, errored, and warning counts;
- first-sync duration;
- second-sync idempotency result;
- conversion exceptions by file type;
- manual correction count and time;
- provenance spot-check pass/fail rate;
- stale or missing source detection after changes;
- reviewed-artifact counts and stale-review counts from `_meta/review-ledger.jsonl`;
- time to answer fixed operational questions before and after Vaultwright;
- operator confidence score;
- support time required.

## Success Matrix

Use this matrix to decide whether a pilot is evidence, partial evidence, or a stop signal:

| Gate | Passing evidence | Stop or fix signal |
| --- | --- | --- |
| Copy-boundary preflight | `sandbox` completed before first sync; any warnings are resolved or explicitly accepted in the private worksheet | The copied vault is the original source root, sits in an unsafe boundary, or has unresolved sandbox errors |
| First sync and front door | `sync --json`, `status --json`, `catalog`, and `catalog --html` complete with manifests/audit evidence captured | Unsupported, conflicted, missing, or error states block the participant's first workflow |
| Conversion and recovery review | High-priority conversion and recovery blockers are resolved or documented before source-backed use | The participant cannot tell which mirrors are safe enough to inspect |
| Agent-readiness benchmark | All task/mode scores exist, cited paths are valid, and prompt-safety review passes strict validation | The result pack has missing scores, uncited scored answers, or unreviewed prompt-safety fields |
| Second sync self-service | The participant runs a second sync without help and confirms no unexpected lifecycle regressions | The operator needs hands-on support for routine refresh |
| Return signal | The participant returns within one week or gives a clear stop reason | No return and no reason, which means the value was not tangible enough |

The review-plan success metric for a tool-shaped product is the second-sync gate: a participant
runs `sync` themselves a second time without help. If three attempts fail on that gate, treat
Vaultwright as a service workflow before treating it as self-serve software.

## Evidence Artifacts

Keep pilot evidence outside this public repository unless it is fully synthetic or public-domain.
For each pilot, maintain an anonymized summary:

- corpus shape, not source contents;
- command transcript with sensitive paths redacted;
- aggregate metrics;
- review-ledger summary, not source or mirror bodies;
- issues found;
- product changes made;
- participant quote only with written permission.

`vaultwright --root "$VW" pilot --json` is designed for machine-readable aggregate evidence.
`vaultwright --root "$VW" pilot --worksheet` prints a redacted Markdown summary for private pilot
records. Both report aggregate counts only, including review-ledger approval/stale-review counts,
and must not be treated as permission to commit pilot evidence to this repository.

## Success Standard

A credible v0.1 needs at least three independent external users and multiple corpora. Passing tests
and public examples are engineering evidence; they do not replace this validation.
