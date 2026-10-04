# PageIndex local validation results

Updated October 4, 2026. MirrorArc remains **unreleased and not accepted for enterprise use**.
This record distinguishes actual runtime checks from model-quality evidence and owner acceptance.
The [release plan](PAGEINDEX_RELEASE_PLAN.md) remains the full finish line.

## What is implemented

The optional PageIndex `0.2.10+mirrorarc.1` worker indexes one registered PDF, validates physical page references,
reuses governed context policies, and publishes immutable evidence. Model calls require an explicit
endpoint, model and command opt-in. The CLI exposes readiness, indexing, questions and status.
The local Catalog presents source-page evidence and unreviewed answer candidates with their frozen
excerpts; it does not run inference or approve claims.

The source revision is upstream `6d23caf416858f2ca136840305d1f479a86f6ef7`, plus the separately
identified [local parser patch and hashed dependency recipe](../src/mirrorarc/document_intelligence/runtime/README.md).
The patched runtime uses Python 3.11.15, pypdf 6.19.0, pypdfium2 5.13.0, LiteLLM 1.103.2,
OpenAI 2.54.0, OpenAI Agents 0.20.0 and HTTPX 0.28.1. The core package does not install this
dependency tree. The local suffix identifies a MirrorArc patch, not an upstream release.

**Original-runtime release blocker, locally mitigated:** a `pip-audit` 2.10.1 audit found
`PYSEC-2026-1835` / `CVE-2023-36464` in PyPDF2 3.0.1. A crafted PDF can cause an infinite loop.
The [upstream advisory](https://github.com/py-pdf/pypdf/security/advisories/GHSA-4vvm-4w3v-6mr8)
lists no patched PyPDF2 release and recommends migrating to maintained `pypdf`. The worker's
timeout limits a hang; it does not patch the parser. The existing runtime is retained as
reproduction evidence, not approved for release or use with untrusted documents. The replacement
removes PyPDF2 entirely, migrates PageIndex's imports to maintained pypdf, and refuses the original
runtime. Provider and parser versions are bound into evidence; an upgrade requires reindexing
and marks older answer candidates historical without overwriting their frozen packs.

Fresh audits reported no known vulnerabilities in published dependencies in either the 81-package
locked provider environment or the 38-package core wheel environment. The local PageIndex patch
and MirrorArc distribution were skipped because those versions are not published on PyPI. This
is not a source-code or native-library security audit. Both environments passed dependency checks.
A separate development-environment audit flagged pytest 9.0.2; that temporary test runtime was
upgraded to 9.0.3 before the final upstream suite. Test tools are not in the optional runtime lock.

## Evidence and limits

| Check | Evidence established | What it does not establish |
| --- | --- | --- |
| Model-free extraction | Actual PageIndex reads a synthetic three-page PDF; physical page 2 contains the expected interval; no model HTTP request | OCR coverage, arbitrary-document conversion quality or answer quality |
| Model-free change trial | Editing 30 days to 14 days invalidates current use; refreshed evidence has a new identity; old frozen bytes survive | A real business-policy change or model reasoning |
| API integration | Actual SDK talks to a scripted loopback peer for assisted indexing and tool-driven questions; selected page text reaches the second question request | Any model's reasoning quality, external endpoint compatibility or paid-provider result |
| Astra context trial | Eight real Codex-subscription cases over synthetic PageIndex-extracted evidence; both plain and governed inputs met the core grounding checks | Better answers than plain text, direct SDK model transport, automatic retrieval, independent judging or release acceptance |
| Boundary enforcement | Invalid configuration, wrong operation/model, output budget, response storage, request size/count, oversized responses, redirects and unapproved Python network/process operations are refused | An OS sandbox, native-parser security audit or dollar-spend guarantee |
| Citation integrity | Source rename, cache tamper and a changed index during pack freezing cannot silently produce mixed-version evidence | Semantic entailment or a guarantee that every claim has sufficient support |
| Parser migration | 321 focused upstream checks; final upstream suite 721 passed, 100 skipped; end-of-file comment regression completes; PyPDF2 absent | Optional Anthropic/Claude integrations or PageIndex cloud tests, which account for the skips; arbitrary hostile PDF safety |
| Reproducible setup | Fresh checkout accepts the packaged patch; hash-enforced dependency install and pinned-backend source build succeed; doctor imports offline | Bit-for-bit reproducible wheel archives or a Linux runtime result |
| Installed package | Fresh core wheel executes doctor, forced indexing, frozen-page export, status and Catalog; all 77 package Python files and four recipe assets match the checkout | Release acceptance or live-provider model behavior |
| Repository integration | Restored checksum-verified CodeGraph 1.5.0; 21-command installed-wheel journey passes source-span, stale/failure, frozen-history and cache-rebuild checks | Whole private-repository coverage or Linux proof |
| Operational recovery | Quiescent 84-file synthetic-vault backup restored at a new path; derived database, PDF index and generated mirror rebuilt; six frozen packs, one reviewed view and one scripted historical answer preserved | A live-writer/cloud-sync backup or restore on the operator's production storage |
| Catalog | Current, stale and damaged candidate states inspected in the browser; keyboard citation expansion; literal script-like text; desktop and 390-pixel text wrapping | Independent-user acceptance or automatic review decisions |

The initial full suite after integration was 580 passed and one optional CodeGraph smoke skipped.
A subsequent hardening run passed 590 tests with that same skip in 261.69 seconds. The combined
hardening suite then passed **591 tests, with one optional CodeGraph smoke skipped**, in 267.46
seconds. Those runs used the original PyPDF2 runtime and did not clear the dependency blocker.
After migration, 24 focused MirrorArc regressions passed. The full suite against the locked
patched runtime passed **593 tests, with one optional CodeGraph smoke skipped**, in 277.33 seconds.
CodeGraph 1.5.0 was subsequently restored in an isolated private folder, with no global installation.
Its Darwin arm64 archive matched the published SHA-256
`cf5ee435a6e44d097b2f98f2b7b8b9422bb1094844404efed82519c5da1af2cf`; all 912 installed files matched
that verified archive. The final combined suite with both optional providers passed
**594 tests, zero skips, in 269.03 seconds**. The current installed wheel also passed the separate
21-command CodeGraph journey. Its source and recipe files still match the checkout; subsequent
edits in this pass are documentation only, not a new package build.

The runtime-validation wheel and sdist built successfully before the later documentation edits.
The wheel SHA-256 is
`cf8bd9d97f06983c129a1b4e5c678b60459d9f2ffc70466ab2a993d0aba8267f` and the sdist SHA-256 is
`15de06b44c28d65d61ae0e94e47bffc92fb314b80321db68c7b3471f3434c7c0`.
The fresh installed-wheel journey preserved the synthetic source and both pre-existing frozen
packs. A second installed-wheel run started with actual legacy-runtime evidence: current use was
refused, reindexing succeeded under pypdf, and all three older frozen packs remained unchanged.
Example-owned shim lint passed for 44 notes / 80 files with all reported warning and error
categories zero. No-data, template-copy and diff-format checks passed. These are local release
checks, not enterprise acceptance.

The durable local review folder is `MirrorArc-Private-Reviews/2026-10-03` under the operator's
Documents directory. `pageindex-proof-06/REVIEW.html` is the earlier model-free owner exercise,
with rendered source-page images because the in-app browser's PDF view was blank. All six PDF
pages were rendered and visually inspected. `wheel-cli-proof-02/proof.json` records the fresh
installed-package journey; `wheel-cli-proof-03/proof.json` records the legacy-to-pypdf migration.
`pageindex-locked-audit.json`, `core-pypdf-wheel-audit.json`,
`pypdf-full-tests.xml` and `pypdf-upstream-all-loopback-tests.xml` retain audit/test evidence.
`answer-ui-proof-02/` is an earlier scripted API/UI contract test, explicitly not model quality.
The historical September Trustworthy Context handoff remains a historical record; its temporary
paths and fingerprints must not be treated as the current shipment evidence.

## Astra subscription trial

On October 4 the owner accepted the shorter authored review layout and authorized testing with
the same model as the planning session through the existing Codex subscription, without a
user-imposed spending cap. These are separate decisions: neither accepts the enterprise release.

Eight real GPT-6 Astra cases completed through Codex CLI 0.160.0 with `max` reasoning effort and
normal ChatGPT authentication. The installed standalone CLI 0.149.0 was refused by the service as
too old for Astra; using the existing app-bundled CLI succeeded without a global upgrade or
credential extraction. This records the tested local versions, not a universal minimum version.

Actual installed MirrorArc and PageIndex generated fresh evidence for three synthetic PDFs.
The harness supplied all three pages either as plain extracted text or as a governed frozen pack.
Both arms received identical page bodies and the same answer instructions. Each arm ran a before,
after, conflicting-evidence and unsupported-question case once. The after case received that arm's
earlier answer as explicitly historical context. All eight runs recorded zero model tool calls;
the harness, not the model, selected the pages. No private source was deliberately supplied.

The planning-session agent inspected every unedited answer against the predeclared rubric and
the rendered source pages. Both arms met the four core grounding checks: 30 days before the edit,
14 days after it, visible 14-versus-30 disagreement without invented precedence, and no invented
purchase price. The fault exception was retained. This was not a blinded or independent evaluation.

| Case | Plain text words | Governed evidence words |
| --- | --- | --- |
| Before | 54 | 61 |
| After | 64 | 69 |
| Conflict | 72 | 73 |
| Unsupported question | 36 | 42 |

Counts are whitespace-separated words in the answer, reason and warning, including citation
markers, not hidden reasoning. Governed answers were slightly longer in every matched case.
**No answer-correctness, comprehension, verification-time or latency advantage was established.**
The independently checked product benefit was traceability: both source edits marked old packs
stale, while earlier frozen bytes remained unchanged before and after inference.

One temporal-wording issue remains: the governed after answer says it “corrects” the prior answer,
although that answer matched the old PDF. Future wording should say the source changed instead
of implying the earlier interpretation was erroneous. The original output remains unedited.

Durable evidence is under `MirrorArc-Private-Reviews/2026-10-04/astra-subscription-trial-01` in the
operator's Documents directory. `trial-spec.json` precedes the calls; `trial-results.json` and the
per-case prompt, answer and event files retain actual inference evidence; `assessment.json` records
the findings; `evidence-proof.json` records source and pack hashes. The passive `REVIEW.html`
contains the actual outputs and linked source-page images. Its default view has 182 visible words;
desktop, 390-pixel width, keyboard disclosure and source-image navigation were checked.
All nine PDF pages were visually inspected. These local artifacts are not public repository data.

This trial did **not** exercise the SDK's direct model-assisted indexing, `document ask` model
transport/publication, automatic evidence selection or production answer UI. The separate
authored-layout approval is recorded in the earlier local review package. Owner judgment of this
real-model report and implementing the accepted layout in the product were still open at that historical checkpoint.
The follow-up below records subsequent runtime changes and new validation separately.

## Answer clarity follow-up — October 4

The actual worker now requests a direct answer, cited reason, visible important caveats and
optional detail. New records label the optional `answer-first-v1` contract while preserving the
complete original output. Backend previews parse only that explicit layout; older or unreadable
layouts fall back to escaped full text with a warning. Catalog puts answer review before general
metadata and document navigation, keeps freshness/unreviewed state visible, and opens frozen
page excerpts from keyboard-accessible citations. No model, freshness calculation or review action
runs in the browser. Default exports omit the question, answer, presentation and excerpts.

New local evidence is in `MirrorArc-Private-Reviews/2026-10-04/clarity-development-01` under the
operator's Documents directory. It is separate from the historical results above:

- The full suite passed **606 tests, with one optional CodeGraph smoke skipped**, in 278.08 seconds.
  The explicit CodeGraph suite then passed all eight tests, including that smoke. The final
  renderer ordering adjustment received the affected focused checks and installed-wheel journey.
- Example-owned shim lint after the documented plan/sync step passed for 44 notes / 80 files with
  all reported issue categories zero. Template-copy, no-data and diff-format checks passed.
- The fresh installed wheel exercised CLI `document ask` with the actual pinned SDK against a
  scripted two-request loopback peer, plus doctor, status and metadata-only Catalog commands.
  All 78 package Python files matched the checkout. Current/stale/damaged Catalog snapshots
  preserve the generated answer and frozen evidence; this is transport/presentation proof.
- The production Catalog was inspected at desktop and 390-pixel widths in current, stale and
  unavailable states. Keyboard citation activation opens and focuses the frozen excerpt,
  script-like text remains literal, and unavailable evidence suppresses the answer. No horizontal
  document overflow was observed. This was developer review, not owner acceptance.
- Five new GPT-6 Astra cases completed through bundled Codex CLI 0.160.0, normal subscription
  authentication, `max` effort and zero model tool calls. The exact product reading instructions
  were tested with the existing synthetic page bodies. Before/after, conflict, unknown price and
  missing change-provenance cases all met the predeclared checks on primary-agent inspection.
  The after case described a verified source change, not a wrong earlier answer. The case without
  comparison evidence refused to establish a change. Raw outputs and prompts are retained.

There was one run per model case, no blinded or independent judge and no new comparison arm.
The harness supplied every page and supplied verified change provenance only to the after case.
This does not establish an answer-quality advantage or validate direct SDK real-model inference.
The earlier eight unedited outputs and their temporal-wording finding remain historical evidence.

Validation setup failures are retained too: a first full-suite invocation used a relative
`PYTHONPATH`, breaking subprocess imports; its 129 failures / 477 passes / one skip are not a
product verdict. The corrected absolute-path invocation produced the result above. The initial
no-data scan caught generated Python/pytest caches, which were moved outside the repository;
subsequent checks used external caches or disabled bytecode. Direct lint of the ungenerated example
reported its expected missing mirrors; the documented copied-example plan/sync/lint journey passed.
An initial UI fixture retained a legacy parser index and was correctly refused until reindexed.

Planning-session acceptance, owner judgment, real SDK model validation, Linux proof and shipment
remain open. No global installation, commit, push, merge, remote change, release or deployment
was performed.

## Backup and recovery evidence

`operational-recovery-03/proof.json`, its command transcript and backup manifest record 28 actual
installed-wheel CLI commands against a synthetic copy. Every one of the 84 backed-up files matched
after restoration at a new path. Database loss and deterministic refresh reattached the reviewed
view, dynamic definitions, all six frozen packs and the PDF index without changing their persisted
evidence. Removing only index JSON and its pointer, while retaining `answers/`, reproduced the
same current index and frozen-pack identities with zero model requests. Moving generated mirrors
aside produced an actionable recovery item; sync recreated the PDF mirror from unchanged source.
Lint and the generated HTML/mirror/reviewed-view no-data scan passed. The input fixture, complete
backup and quarantined recovery evidence were preserved.

The semantic relationship-review decision was deliberately absent after source-only database
reconstruction, then recovered exactly by restoring the database backup. The reviewer name was
explicitly a synthetic fixture, not owner approval. The historical answer was produced by an
earlier scripted loopback peer, not a real model. These distinctions are part of the proof.

The initial sandbox had zero errors and retained warnings: no repository manifest was needed in
the PDF-only vault, and the private review directory is inside an unrelated parent Git workspace.
The evidence files were verified untracked there; no files were staged, committed or published in
that parent repository. Keep backups outside publication paths and repeat the drill on actual
pilot storage.
The first drill attempt stopped because the harness added native Markdown without explicitly
refreshing deterministic relationships. The corrected run performs that documented step; this was
a harness correction, not a hidden product fix.

Additional durable evidence is `all-providers-full-tests.xml`, `codegraph-wheel-journey-01/journey.json`,
`codegraph-1.5.0-proof/` and the private `validate_operational_recovery.py` drill. The recovery guide
now distinguishes index maintenance from answer-history retention and database restoration from
source-only reconstruction.

## What remains before release

1. Complete real-model validation of the supported SDK indexing/question workflow. The approved
   Codex evidence trial is complete; do not ask again for its model or spending cap or present it
   as proof of the untested direct SDK route. Any different inference route needs explicit scope.
2. Review and accept the locally implemented concise presentation and temporal-wording instructions
   in the actual product. Obtain owner judgment of actual generated answers and verification
   effort; the authored-layout approval and eight-case self-review cannot supply that judgment.
3. Re-audit at shipment and review maintenance of the local provider patch. Complete Linux
   validation and deployment hardening. The local synthetic restore drill is complete; the
   operator runbook requires repeating it on actual storage before a production deployment.
   The October 3 check found no available Docker daemon or Colima instance. Linux testing is
   deferred for the Mac owner pilot, not removed from release requirements; no VM was created.
4. Review the combined dirty tree and its final fingerprint. Keep pre-existing changes in scope
   rather than treating the current HEAD as a complete description of the work.
5. Obtain acceptance and confirm shipment scope. The current workflow definitions were inspected:
   PR/main activity can run hosted CI, this batch matches the main-branch Pages deployment paths,
   and `v*` tags trigger a draft prerelease. Resolve those automatic effects before the single
   owner-authored PR/merge, then rebuild final artifacts from the accepted tree. No commit, push,
   workflow edit, remote-setting change, release or deployment was performed in this validation pass.

The request-attempt guard follows the distinction between per-attempt timeouts and total retry
budgets in [official OpenAI rate-limit guidance](https://developers.openai.com/api/docs/guides/rate-limits).
Provider-side budget and retention controls still require operator review.
