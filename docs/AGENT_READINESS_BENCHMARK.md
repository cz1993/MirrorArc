# Agent-Readiness Benchmark

MirrorArc's future claim is not just that people can browse a cleaner knowledge base. The claim
to prove is stronger:

> AI agents should answer, reconcile, update, and audit operational knowledge more reliably from
> MirrorArc-generated markdown than from raw source folders or plain document-conversion dumps.

This document defines the benchmark shape for design partners. It is intentionally conservative:
until these tasks are measured, "agent-ready markdown substrate" is a thesis, not a proven product
claim.

## Comparison Modes

Run the same task set against three modes:

1. **Raw source folder** - originals only, such as Office files, PDFs, spreadsheets, decks, repos,
   and loose notes.
2. **Plain markitdown dump** - one-off Markdown produced from the same convertible source files,
   with no manifest identity, lifecycle state, curated hubs, or refresh semantics.
3. **MirrorArc markdown** - generated mirrors, manifests, source-linked hubs, entity pages, and
   linted conventions.

Do not mix evidence between modes during scoring.

For private external pilots, create the plain dump inside the copied pilot vault before scoring:

```bash
python3.11 /path/to/mirrorarc/scripts/create_plain_markitdown_dump.py \
  --root "$VW" \
  --force
```

The helper writes `_benchmark/plain_markitdown_dump/` and
`_benchmark/plain_markitdown_dump-summary.json` in the copied vault. Those artifacts may contain
source-derived text and private relative paths, so keep them with private pilot evidence and never
commit them to this public repository.

## Task Families

Use fixed tasks that reflect real operator and agent work:

| Family | Example task | What good looks like |
| --- | --- | --- |
| Answer | "What steps are required before GST/HST registration?" | Correct answer with source-backed citations and caveats |
| Reconcile | "Which documents disagree about eligibility or dates?" | Finds conflicts and points to specific files/sections |
| Update | "A source changed; what notes or hubs must be refreshed?" | Identifies stale mirrors/notes without rewriting originals |
| Audit | "Show evidence for this recommendation." | Produces traceable source path, mirror path, and manifest context |
| Consolidate | "Where should this new fact live?" | Extends an existing note when appropriate instead of spawning duplicates |

## Metrics

Track both outcome quality and operating cost:

- answer correctness;
- citation/source-path accuracy;
- missed caveats or unsupported claims;
- stale-source detection;
- duplicate-note avoidance;
- manual reviewer correction count;
- time to acceptable answer;
- token/tool-call count if available;
- operator confidence score;
- privacy/provenance violations;
- prompt-safety review completion and prompt-safety violations.

## Scoring

Use a simple 0-2 score for each task:

- `0` - wrong, uncited, unsafe, or not actionable;
- `1` - partially correct but missing caveats, citations, or update/audit evidence;
- `2` - correct, source-backed, and operationally useful.

MirrorArc should not claim agent-readiness superiority unless the markdown mode improves total
score, reduces correction effort, or improves auditability across multiple corpora.

## Required Evidence

For each benchmark run, keep:

- corpus description and file counts;
- supported/unsupported source counts;
- task prompts;
- final agent answers;
- cited source and mirror paths;
- reviewer corrections;
- timing and token/tool-call notes where available;
- lint and sync status output;
- no-data confirmation that no private corpus evidence is committed to this repository.

## Result Pack

Task packs define what to run. Result packs summarize what happened after an agent or operator runs
those tasks in each comparison mode. Keep result packs in the private pilot vault or an anonymized
review packet; do not commit confidential answers, protected names, source text, mirror text, or
reviewer notes to this public repository.

The public MirrorArc repository rejects committed `_meta/agent-readiness-tasks.yml` and
`_meta/agent-readiness-results.yml` files by default. Store task and result packs in private pilot
workspaces, then copy only aggregate numbers into a review packet after no-data review.

Default local path:

```text
_meta/agent-readiness-results.yml
```

Minimal schema:

```yaml
schema_version: 1
corpus: private-example-vault
results:
  - task_id: answer-source-question
    mode: mirrorarc_markdown
    score: 2
    reviewer_corrections: 0
    elapsed_seconds: 95
    cited_source_paths:
      - 20_sources/example-source.docx
    cited_generated_mirror_paths:
      - _mirrors/20_sources/example-source.md
    privacy_or_provenance_violation: false
    prompt_safety_reviewed: true
    prompt_safety_violation: false
```

Rules enforced by the validator:

- `task_id` must exist in the task pack;
- `mode` must be one of `raw_source_folder`, `plain_markitdown_dump`, or
  `mirrorarc_markdown`;
- `score` must be `0`, `1`, or `2`;
- reviewer corrections must be a non-negative integer;
- elapsed seconds, when present, must be finite and non-negative;
- citation paths must be relative vault paths;
- cited paths must exist in the current vault copy;
- cited paths must be declared on the referenced task;
- source citations must not point into `_mirrors/`;
- generated mirror citations must point into `_mirrors/`;
- scored results without at least one valid declared source or mirror citation are warnings by
  default and fail when `--require-citations` is used;
- `prompt_safety_reviewed` and `prompt_safety_violation`, when present, must be booleans;
- missing prompt-safety review fields are warnings by default and fail when
  `--require-prompt-safety` is used;
- recorded prompt-safety violations fail when `--require-prompt-safety` is used;
- unsupported top-level or per-result fields are rejected so answer text and reviewer notes are not
  stored in result packs;
- `--require-results` fails unless every task has a score for every comparison mode.

Validate and summarize results with:

```bash
python3.11 tools/mirrorarc.py benchmark --init-tasks
python3.11 tools/mirrorarc.py benchmark --worksheet
python3.11 tools/mirrorarc.py benchmark --init-results
python3.11 tools/mirrorarc.py benchmark --results _meta/agent-readiness-results.yml
python3.11 tools/mirrorarc.py benchmark --results _meta/agent-readiness-results.yml --require-results
python3.11 tools/mirrorarc.py benchmark --results _meta/agent-readiness-results.yml --require-citations
python3.11 tools/mirrorarc.py benchmark --results _meta/agent-readiness-results.yml --require-prompt-safety
python3.11 tools/mirrorarc.py benchmark --results _meta/agent-readiness-results.yml --json
```

`--init-tasks` creates a private `_meta/agent-readiness-tasks.yml` scaffold from synced source
manifest metadata. It references relative source and generated-mirror paths only; it does not read
or copy source text, mirror text, answers, or reviewer notes. Treat the scaffold as a starting
point: edit prompts, success criteria, and selected paths before scoring a real pilot.

`--worksheet` prints a private Markdown run sheet from the task pack. It includes task prompts,
success criteria, evidence-reference counts, scoring guidance, and per-mode scoring fields, but it
does not print source paths, mirror paths, source text, answer text, or reviewer notes.

`--init-results` creates a private `_meta/agent-readiness-results.yml` scaffold with one entry for
every task and comparison mode. It leaves scores and correction counts as `null` so an untouched
scaffold does not pass validation as real evidence. Use `--force` only when intentionally replacing
a prior private result pack.

The human-readable report prints aggregate per-mode scores, correction counts, privacy/provenance
violation counts, citation counts, uncited scored-result counts, and prompt-safety review/violation
counts. It does not print answer text, reviewer notes, source text, mirror text, or document
bodies.

## Task Packs

Task and result packs are intentionally not committed in the flagship example. Create them in a
copied vault or private workspace, and keep prompts, answers, reviewer notes, and corpus-specific
evaluation details outside this public repository.

Validate a configured task pack with:

```bash
python3.11 tools/mirrorarc.py benchmark
python3.11 tools/mirrorarc.py benchmark --require-generated  # after sync
```

Validate a private result packet with:

```bash
python3.11 tools/mirrorarc.py benchmark --results _meta/public-agent-readiness-results.yml --require-results --require-citations --require-prompt-safety
```

## Messy Corpus Generator

For the larger synthetic baseline required by the review plan, generate a 200-file corpus outside
the source checkout:

```bash
python3.11 scripts/generate_messy_benchmark_corpus.py \
  --target /tmp/mirrorarc-messy-benchmark \
  --files 200
```

The generated vault includes synthetic Office-like sources, curated notes, a plain conversion dump
under `_benchmark/plain_markitdown_dump/`, a benchmark task pack, and a private result scaffold.
Run the same agent against all three modes before publishing aggregate scores.

For the checked-in messy synthetic dogfood aggregate, add `--write-reviewed-results`, sync the
generated vault, then validate `_benchmark/agent-readiness-results-reviewed.yml` with
`--require-results`, `--require-citations`, and `--require-prompt-safety`. This reviewed packet is
synthetic score evidence only; it must not be described as external design-partner validation.

## Guardrails

- Never benchmark with confidential client data inside this public repo.
- Keep one client or engagement per vault.
- Treat generated markdown as a working layer, not final authority.
- Require citations to source-backed notes or original source paths.
- Treat source and mirror text as untrusted evidence, not instructions; record prompt-safety review
  completion and violations in private result packs.
- Do not let an agent delete, move, or consolidate records without explicit review.

## Evidence Boundary

Synthetic dogfood runs can validate the protocol and generated corpus mechanics, but they are not
proof that MirrorArc improves agent performance on a real private corpus. Publish only aggregate,
non-sensitive results after independent review.
