# PageIndex document review

MirrorArc can use PageIndex to navigate a registered PDF by physical page and export page-linked
evidence. Model-free indexing is available without credentials. Optional model-assisted indexing
and questions require a deliberately configured endpoint and per-command approval. This integration
is under local validation; it is not yet an accepted enterprise release.

## Install the optional runtime

Keep PageIndex separate from MirrorArc's core Python environment. Plain upstream `0.2.10`
installs vulnerable PyPDF2 and is refused. The tested local patch is distinctly labeled
`0.2.10+mirrorarc.1` and uses maintained `pypdf` 6.19.0. This is a MirrorArc compatibility patch,
not an upstream release. Its source, license and dependency hashes are included in the
[runtime recipe](../src/mirrorarc/document_intelligence/runtime/README.md).

Start in a new setup directory outside the vault and public repository. Use the Python that has
MirrorArc installed to find its packaged recipe. The following commands download public source
and packages into a separate local environment, not a global installation:

```bash
MIRRORARC_PAGEINDEX_ASSETS="$(python -c 'from importlib.resources import files; print(files("mirrorarc.document_intelligence") / "runtime")')"
git clone https://github.com/VectifyAI/PageIndex.git PageIndex-local
git -C PageIndex-local checkout --detach 6d23caf416858f2ca136840305d1f479a86f6ef7
git -C PageIndex-local apply --check "$MIRRORARC_PAGEINDEX_ASSETS/pageindex-pypdf.patch"
git -C PageIndex-local apply "$MIRRORARC_PAGEINDEX_ASSETS/pageindex-pypdf.patch"
uv venv .pageindex-runtime --python 3.11
uv pip install --python .pageindex-runtime/bin/python --require-hashes --only-binary=:all: \
  -r "$MIRRORARC_PAGEINDEX_ASSETS/requirements-py311.txt"
uv pip install --python .pageindex-runtime/bin/python --no-deps --no-build-isolation ./PageIndex-local
uv pip check --python .pageindex-runtime/bin/python
export MIRRORARC_PAGEINDEX_PYTHON="$(pwd)/.pageindex-runtime/bin/python"
mirrorarc --root /absolute/path/to/copied-vault document doctor
```

The dependency lock and patched-source installation have been exercised on macOS with Python
3.11; universal resolution alone does not verify Linux. PageIndex brings model/agent dependencies, including an MCP
library, but MirrorArc does not start an MCP service, watcher or daemon. It uses the pinned local
SDK, not the PageIndex managed cloud. Upstream uses the MIT license; MirrorArc remains AGPL.
The readiness command loads the required extraction and API libraries with networking disabled
and reports their versions. It does not contact a model or prove that an endpoint supports the
configured model. A matching package-version label alone is not enough to report Ready.

## First review without a model

1. Start with a copied vault containing a PDF you are allowed to process. Run `mirrorarc sync`
   and `mirrorarc relationships refresh` so the source and its identity are registered.
2. Read the source ID from `mirrorarc status --json`.
3. Index the PDF, then export the physical pages you want to inspect:

   ```bash
   mirrorarc --root /absolute/path/to/copied-vault document index --source SOURCE_ID
   mirrorarc --root /absolute/path/to/copied-vault document index --source SOURCE_ID \
     --context frozen --page 2
   mirrorarc --root /absolute/path/to/copied-vault catalog --html --include-content
   ```

4. Open the generated `CATALOG.html`, choose the PDF, and select **Document metadata**.
   The **PDF page evidence** section shows its status, source hash, structure and bounded page
   excerpts. Expand a physical page to read its text. Without `--include-content`, the Catalog
   contains status and references only. Content-enabled HTML must be protected like the source.
5. Use `document status --json` after a source change. Sync and reindex before using current
   evidence. Earlier frozen packs retain their original bytes and hashes.

Flash's structure-only mode is model-free. It is not OCR, a semantic answer, or a guarantee that
all text, figures and layout were extracted. Scanned PDFs and documents whose structure Flash
cannot handle receive an actionable refusal. Do not silently substitute empty evidence.

## Approve a model explicitly

Create a local `_meta/pageindex.yml` with these fields, replacing the model, endpoint and variable
name with an approved configuration. Do not put credentials in the file.

```yaml
model: your-approved-model-id
base_url: https://your-approved-endpoint.example/v1
api_key_env: MIRRORARC_APPROVED_MODEL_KEY
max_requests: 8
max_output_tokens: 1024
max_request_bytes: 100000
```

Set the named credential through your shell or credential manager. Indexing uses an
OpenAI-compatible Chat Completions endpoint; questions use an OpenAI-compatible Responses endpoint
with tool calling. An endpoint supporting only one protocol does not support both workflows.
Local inference is possible only when the operator's server provides the required protocol.
HTTP is accepted on loopback only; remote endpoints require HTTPS.

```bash
# Optional model-generated structure optimization and summaries:
mirrorarc --root /absolute/path/to/copied-vault document index --source SOURCE_ID \
  --model-assisted --allow-model

# Optional slower model-based indexing when Flash refuses a readable document:
mirrorarc --root /absolute/path/to/copied-vault document index --source SOURCE_ID \
  --mode standard --model-assisted --allow-model

mirrorarc --root /absolute/path/to/copied-vault document ask --source SOURCE_ID \
  --question "What is the inspection interval, and what exceptions apply?" \
  --allow-model --json
```

Approving a model operation permits sending bounded source text and the question to that configured
endpoint. It can incur charges. The worker strips ambient credentials/proxies, disables dotenv
loading and tracing, restricts Python network destinations, limits HTTP request count and size,
bounds output, and has a total deadline. These controls are not an OS security sandbox or a
dollar-spend guarantee; a request already accepted by a provider may remain billable after a local
timeout. Use provider-side budget controls too.

Questions produce an **unreviewed answer candidate** with validated document/page addresses and a
frozen evidence pack. If cited pages do not fit the current context policy, answer publication
fails rather than implying the pack contains all cited evidence. The candidate JSON and index
cache live under ignored `.mirrorarc/cache/pageindex/`. Citation validity means the page exists
in the recorded source, not that the claim is true. Human review must check claim support,
exceptions, conflicting evidence and whether the document reflects deployed policy.

## Review an answer in the Catalog

After asking a question, regenerate the local Catalog with `catalog --html --include-content`.
Choose the PDF and open **Document metadata**. **Answer review** appears before document
navigation. New conforming answers show the direct **Answer**, short source-linked **Reason**,
and **Important** exceptions, disagreement or uncertainty without a disclosure. Follow a physical
page link to open and focus its frozen excerpt with either a mouse or keyboard. **Additional
detail**, the **Complete original generated answer**, and provenance are optional disclosures. The displayed excerpts come from the answer's hash-checked frozen pack, not a newer PDF.

New answer records declare the optional `answer-first-v1` presentation contract. The worker asks
for exactly `Answer:`, `Reason:`, `Important:` and `Details:` headings in that order; the backend
recognizes those explicit sections and checked citation addresses without summarizing or guessing.
The reason must contain a page citation and every section must contain text (`None.` is allowed
for details). Older records, unknown contracts and malformed layouts display the escaped complete
original with a warning. The immutable candidate always retains the exact generated answer;
regenerating Catalog does not restyle saved history or overwrite reviewed views. This structural
check does not detect every omitted caveat or verify semantic claim support.

Instructions distinguish a source change from a wrong earlier answer: a source-correct historical
answer is not an error just because newer evidence differs. Source-change wording requires supplied
evidence or provenance; without it, comparison is unavailable. The browser does not infer a change.

**Current** means the source and index still match; it is not a correctness score or approval.
**Stale** means the old answer must be reconsidered against changed or unavailable source or
indexed evidence, including a parser upgrade.
**Unavailable** means the candidate or frozen pack failed inspection, so its text is not shown.
The Catalog is a saved snapshot, not a live monitor: regenerate it after source changes.

The default metadata-only Catalog omits questions, answers and page excerpts. Content-enabled
Catalogs show a bounded selection of at most five candidates per source, not necessarily the newest
five. Answer text (including duplicated structured/original presentation), questions and frozen excerpts share the 100,000-character overall PDF-content
budget. A full candidate that does not fit is omitted rather than displayed with missing citations.
The browser does not send a model request, save a review decision or promote an answer to authority.

## Limits and recovery

Limits are 32 MiB per PDF, 500 physical pages, 2 MB of extracted text, 2,000 tree nodes and depth
16, plus existing profile context ceilings. Catalog previews include at most 100 nodes and 20,000
text characters per PDF, with a 100,000-character total page-text budget. Truncation and omitted
pages are visible. Frozen page entries also use the profile `max_files` ceiling conservatively.
Model configuration is limited to 16 KiB and refuses duplicate fields. HTTP calls are restricted
to the approved model and either Chat Completions indexing or Responses questions; each must carry
an output-token limit and `store: false`. Request attempts are counted at the HTTP boundary,
including retries, and decoded response bodies are limited to 2 MB. The worker refuses Python
subprocess execution and redirects. These controls do not guarantee provider retention behavior,
claim support, or isolation against hostile native code.

Failed indexing retains the last valid pointer. A changed source, parser contract or tampered
cache is refused. After upgrading from the original PyPDF2 runtime, install a fresh isolated
environment and reindex; previous frozen evidence remains historical and byte-for-byte intact.
Model-generated summaries remain derived navigation; they never overwrite the L1 projection or
a reviewed view. Back up sources, manifests, the SQLite review ledger, reviewed artifacts, frozen
packs and saved answer candidates before cache maintenance. Preserve the selected source's
`answers/` directory: model-free indexing cannot recreate its historical answers. Move only the
index JSON and current pointer aside when rebuilding an index. See the
[recovery guide](RECOVERY.md#rebuild-pdf-indexes-without-losing-answer-history) for the tested
restore boundary. Reindexing in model-assisted mode can incur fresh charges.

The [release plan](PAGEINDEX_RELEASE_PLAN.md) and [local validation results](PAGEINDEX_RESULTS.md)
track real-model evaluation, human review, platform proof, packaging and final shipment separately
from local contract tests.
