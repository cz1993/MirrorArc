# PageIndex integration and MirrorArc release plan

The October 3, 2026 operator goal is to integrate VectifyAI PageIndex and finalize MirrorArc
for an enterprise release after self-testing and review. This extends the earlier Trustworthy
Context batch, which treated PageIndex as a reference only. It does not authorize private-source
transmission, paid inference, changing remote settings, or deploying the public demo implicitly.
On October 4 the owner explicitly approved testing Astra through the existing Codex subscription
without a user-imposed spending cap. That test authorization does not approve private-source
transmission, a different paid API route, publication, or removal of runtime safety limits.

Release is not yet accepted. Passing synthetic tests or installing PageIndex is not sufficient.
The intended result is an inspectable document-to-answer workflow with source preservation,
page citations, change detection, governed context, a usable review UI, and operational evidence.
Enterprise readiness is limited to the documented local deployment model, not a claim of a
multi-tenant service, compliance certification, or independently audited security.

## Integration contract

- Keep originals, existing source identities, lifecycle and relationship state authoritative.
- Use the actual optional PageIndex local runtime, pinned to a verified version. Do not add a
  vector database, cloud document upload, daemon, MCP server, second watcher, or lifecycle store.
- Keep PageIndex's dependency tree out of MirrorArc's core install. Its SDK has transitive
  agent/MCP dependencies; installing them must not start a service or alter agent configuration.
- Support PageIndex Flash's model-free PDF structure extraction and an explicitly approved
  model-assisted indexing and question-answering path. The former is not evidence of model quality.
- Require an explicit model, endpoint and credential environment-variable name for model calls.
  Clear ambient provider credentials and tracing configuration in the isolated worker. Never
  save a key in the vault or logs. Bound subprocess time, output, documents and model execution.
- Validate page numbers and source hashes independently of model assertions. Generated headings,
  summaries and answers remain unreviewed candidates; an addressable citation does not prove
  that the cited page supports a claim.
- Reuse existing context policies and immutable frozen packs. Source changes invalidate current
  use while preserving historical bytes. Failed refreshes preserve the previous valid result.
- Present source, page, freshness, evidence, warnings and next action in the passive Catalog.
  No model call or process launch from HTML. Keep default exports metadata-only.

## Execution and acceptance

| Area | Required evidence | Current state |
| --- | --- | --- |
| Frozen history | Effective-budget change, repeated freeze, recovery and tamper refusal for code and document packs | Focused regressions pass locally |
| Retrieval capacity | One useful hit retained with 120 and 500 candidates; full diagnostics available separately | Focused regressions pass locally |
| Upstream contract | Pinned actual SDK, real PDF extraction, error/limit behavior, license and dependency inventory | Original PyPDF2 vulnerability mitigated by distinct local 0.2.10+mirrorarc.1 patch using pypdf 6.19.0; hashed install and published-dependency audit pass locally; patch maintenance remains a review item |
| Integration | CLI readiness/index/question/status, confinement, provenance, stale state, governed contexts | Implemented locally; actual extraction and both API transport contracts exercised without a real model |
| Model-assisted SDK workflow | Approved endpoint, bounded calls, real indexing and answer with validated citations | Direct SDK model-assisted indexing and question transport have not run against a real model; the separate Codex trial does not close this gate |
| Astra context trial | Actual model answers over PageIndex-extracted evidence, compared with identical plain-text page bodies | Eight subscription-backed cases completed October 4; both arms met core grounding checks, with no answer-quality advantage demonstrated and one temporal-wording finding |
| Human review | Durable working UI and before/after report, exact evidence, conflict and uncertainty labels | Owner accepted the shorter authored review layout October 4; answer-first product layout implemented locally; planning-session review and owner judgment remain open |
| Safety and recovery | Policy denial before content access, malicious input, no source mutation, failure preservation, cache rebuild | Synthetic installed-wheel whole-vault restore and derived database/PDF-index/mirror rebuild pass; actual-storage restore and hostile-native-parser isolation remain |
| Local release gate | Full suite, example shim lint, no-data, templates, build and installed-wheel journeys | 594 passed / no skips with both optional providers; installed-wheel PageIndex, CodeGraph and recovery journeys pass; current evidence is in PAGEINDEX_RESULTS.md, not release acceptance |
| Platform and operations | macOS and Linux proof or explicit unsupported scope; install, backup, restore and support documentation | macOS evidence only; Linux testing is deferred for the Mac owner pilot, not removed from the cross-platform release gate |
| Shipment | Review accepted; owner identity; inspect CI, Pages and release triggers; one consolidated PR/merge | Not authorized before acceptance |

## Model and publication decisions

The approved test route is GPT-6 Astra through the existing Codex subscription, using synthetic
or suitably licensed public inputs. The October 4 trial used synthetic PDFs only. Normal CLI
authentication remains inside Codex; do not extract credentials or turn the subscription into an
undocumented API gateway. No separate endpoint or spending-ceiling decision is needed to repeat
this approved test route. It does not remove product request, output, source-access or time limits.

The currently implemented SDK model path is different: it requires explicit model, endpoint and
credential configuration. Its real-model validation remains open. Do not silently substitute the
Codex evidence trial for that gate, switch to another paid provider, or transmit private source
content. No private LG MAP source is required for PageIndex validation.

Final publication must distinguish the consolidated code PR/merge from a versioned package
release and public demo deployment. Do not equate an unanswered approval question with consent.
Local development and the authorized synthetic Codex tests can continue meanwhile.

## Development follow-up after the Astra trial

The [measured results](PAGEINDEX_RESULTS.md#astra-subscription-trial) are a small, non-blinded
comparison, not evidence of general answer superiority. The bounded development slice is implemented locally and awaits planning-session acceptance, as
specified in the [new-session prompt](prompts/PAGEINDEX_CLARITY_FOLLOWUP.md):

1. Carry the accepted outcome-first layout into generated answers and the actual Catalog. Keep
   a short source-linked reason and important disagreement, uncertainty or exceptions visible;
   place supporting evidence behind disclosure without losing the complete original candidate.
2. Distinguish a changed source from a mistaken earlier answer. An answer that matched its old
   evidence must not be labeled wrong merely because the source changed.
3. Verify the real product UI and response contract, including old answer compatibility, safe
   rendering, citations, stale state and metadata-only exclusion. Keep the live Codex trial
   separate from direct SDK inference and from the full local release gate.

This planning session remains responsible for post-development review. Layout approval is not
approval to ship. Linux validation remains a later release requirement; no test VM is authorized
merely by deferring it for the Mac pilot.

## Shipment trigger review

The working-tree workflow definitions were inspected on October 3. This is not a claim about live
GitHub branch protections or account permissions, which must be verified at the shipment checkpoint.

| Local workflow | Trigger | Consequence to resolve before shipment |
| --- | --- | --- |
| `.github/workflows/ci.yml` | PR activity and pushes to `main`; draft PR test job is skipped | A ready PR or final merge can start hosted CI; local validation does not disable the trigger |
| `.github/workflows/pages.yml` | Relevant pushes to `main`, including source/package/example changes; manual dispatch | The current batch matches those paths, so merging can deploy the public demo |
| `.github/workflows/release.yml` | Tags beginning with `v` | Builds artifacts and creates or updates a draft prerelease; an ordinary branch merge does not trigger it |

Do not push, tag or merge until the owner resolves hosted runs and demo deployment explicitly.
For a shipment with no automatic hosted runs, review manual-only workflow changes before the final
push. No workflow definition or remote setting was changed by this inspection.

## Owner review package

Store private or generated review evidence in a durable local folder outside the publication
tree, not in `/tmp`. Include an entry page, Catalogs for before/after/stale states, the question,
both answers, claim-linked source excerpts, a description of the controlled change, and a short
feedback form. Explicitly label model output versus authored expected answers. The owner judges
whether the second answer is easier to verify and safer to trust; no real customer is required
for this owner-assisted pilot, but it is not an independent-user study.

## Upstream evidence

Inspected [PageIndex](https://github.com/VectifyAI/PageIndex) commit
`6d23caf416858f2ca136840305d1f479a86f6ef7`, reporting version `0.2.10`, under MIT.
The required local patch changes the distribution to `0.2.10+mirrorarc.1`, migrates PyPDF2 imports
to pypdf and retains upstream behavior. It is not an upstream release. Plain `0.2.10` is refused.
The local SDK accepts PDFs. `page_index_flash(summary=False, optimize=False)` is model-free;
ordinary SDK document submission generates summaries and can call a configured model. Local
storage therefore does not imply offline inference. The upstream project is labeled Alpha;
MirrorArc cannot promote that dependency to a production guarantee by relabeling it.

Model-call retry policy must account for nested SDK retries and a total deadline, not only a
per-request timeout. See [OpenAI rate-limit guidance](https://developers.openai.com/api/docs/guides/rate-limits).
