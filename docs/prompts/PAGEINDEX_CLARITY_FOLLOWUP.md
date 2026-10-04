# PageIndex answer clarity development prompt

Work in the existing dirty MirrorArc checkout. This is a bounded development follow-up to the
October 4 owner review and Astra trial, not authorization to release. Keep the originating chat
as the planning and post-development review session. Do not create or message another chat unless
the owner explicitly asks; this document is a prompt the owner can use in a new session.

Read `AGENTS.md`, `README.md`, `docs/PRODUCT.md`, `docs/PAGEINDEX.md`,
`docs/PAGEINDEX_RELEASE_PLAN.md` and `docs/PAGEINDEX_RESULTS.md` before editing. Preserve all
pre-existing changes. Inspect actual behavior before assuming a gap.

## Required result

Apply the owner-approved reading pattern to the actual PageIndex answer workflow and Catalog:
answer first, a short source-linked reason, visible important disagreement or uncertainty, then
optional detailed evidence. The accepted report is a design reference, not already implemented
product behavior. Keep the approach industry-neutral.

The real Astra trial found no correctness advantage over identical plain-text evidence; both arms
passed its core checks. Do not turn those results into a claim of superior reasoning. It also
found a wording problem: saying the new answer “corrects” an earlier source-correct answer can
misrepresent history. Say the source changed unless the old answer was actually wrong for its
recorded evidence. Do not assert a source change without the relevant evidence or provenance.

## Implementation boundaries

- Start with the existing worker instructions, answer record, backend preview and Catalog
  renderer. Keep the change small; do not add a provider framework, database, watcher or daemon.
- Keep citations, important exceptions, uncertainty, freshness and unreviewed status visible.
  Do not obtain brevity by silently dropping evidence or by hiding the entire answer's risks.
- Preserve the complete generated answer and its immutable frozen evidence. Never rewrite
  historical outputs or a reviewed view merely to apply the new style.
- Support existing answer records. If a proposed structured presentation cannot be safely read,
  display the escaped original with an honest warning; do not guess missing fields or authority.
- Keep default exports metadata-only. The browser remains passive: no inference, network fetch,
  local process launch, automatic review or independent freshness calculation.
- Do not extract Codex credentials, create a subscription-to-API proxy, or weaken request/output
  limits. The approved subscription route is for synthetic evidence trials; the current direct
  SDK route still needs real-model proof. Do not silently replace one with the other.

## Validation and handoff

Add focused tests for the changed response/presentation contract, old-record compatibility,
safe rendering, citations and content exclusion. Exercise the actual generated Catalog with
current, stale and unavailable answers, using keyboard and narrow-width checks. Do not substitute
a standalone mock review page for the production UI.

For an authorized Astra test, use normal Codex subscription authentication with synthetic or
suitably licensed public inputs only. Verify the available CLI can actually invoke Astra rather
than trusting a model listing. Keep source access minimal and retain the prompts, exact outputs,
versions and limitations outside the public repo. Score changed evidence, conflict and unknown
answers honestly; preserve failures and do not replace measured outputs with authored examples.

Update the changelog and relevant docs for behavior actually delivered. Run focused tests during
development; near completion run the full existing local suite, package-owned example lint,
template-copy and no-data checks, then the affected installed-wheel journey. Report new evidence
separately from historical passes. Linux proof is deferred for the Mac pilot, not removed from
the eventual cross-platform release gate.

Return the exact changed files, commands/results, actual Catalog review entry point, model-test
scope, remaining limitations and final dirty-tree fingerprint to the planning session. Do not
stage, commit, push, merge, deploy, release, alter remote settings or install globally. Local
completion still requires planning-session acceptance before the single owner-controlled shipment.
