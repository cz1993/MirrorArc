# Agent-Readiness Benchmark Results

This page publishes aggregate benchmark evidence that is safe to keep in the public repository.
Private answer text, reviewer notes, source bodies, mirror bodies, and client-specific task packs
must stay outside this repo.

## 2026-07-03 Public Synthetic Dogfood

This is the first review-plan baseline run. It uses the public synthetic
`examples/government-services-vault` corpus and the task pack at
`examples/government-services-vault/_meta/agent-readiness-tasks.yml`.

It is **not external validation**. It is a dogfood run on a synthetic corpus so the project has a
published three-condition benchmark packet before design-partner work begins. The decision rules
for external benchmark evidence are tracked in [`docs/VALIDATION_GATE.md`](VALIDATION_GATE.md).

### Conditions

| Mode | Description |
| --- | --- |
| `raw_source_folder` | Original files and committed notes only. |
| `plain_markitdown_dump` | One-off Markdown conversion baseline without NoeticWeave manifests, lifecycle state, or curated mirror workflow. |
| `noeticweave_markdown` | NoeticWeave task context: source-linked curated notes plus generated mirror workflow and manifest/lifecycle semantics. |

### Aggregate Scores

| Mode | Results | Score | Average | Reviewer corrections | Privacy/provenance violations | Prompt-safety reviews |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `raw_source_folder` | 6 | 5 / 12 | 0.83 | 7 | 0 | 6 / 6 |
| `plain_markitdown_dump` | 6 | 6 / 12 | 1.00 | 6 | 0 | 6 / 6 |
| `noeticweave_markdown` | 6 | 12 / 12 | 2.00 | 0 | 0 | 6 / 6 |

### What The Scores Mean

The synthetic run mostly measures whether the public task protocol can distinguish operational
workflows that need more than extracted text:

- answer tasks can usually be partially completed from raw files or a plain conversion dump;
- update and audit tasks need manifest/lifecycle context to identify generated mirrors and review
  targets reliably;
- consolidation tasks benefit from the curated hubs and anti-proliferation rules.

The result packet is intentionally aggregate-only:
`examples/government-services-vault/_meta/public-agent-readiness-results.yml`.

Validate it from the example vault:

```bash
python3.11 tools/noeticweave.py benchmark \
  --results _meta/public-agent-readiness-results.yml \
  --require-results \
  --require-citations \
  --require-prompt-safety
```

Expected summary:

```text
raw_source_folder: results=6 score=5/12 avg=0.83 corrections=7 violations=0
plain_markitdown_dump: results=6 score=6/12 avg=1.00 corrections=6 violations=0
noeticweave_markdown: results=6 score=12/12 avg=2.00 corrections=0 violations=0
```

### Limits

- This is synthetic dogfood evidence, not a design-partner result.
- Timing and token/tool-call counts were not captured in this packet.
- Generated mirror citations are omitted so the public result pack validates against the committed
  example tree without committing generated mirrors.
- The next benchmark step is a messy larger corpus and a real external design-partner run using
  the same task/result schema.

## Messy Synthetic 200-File Corpus

The review plan requires a messier synthetic corpus before treating the benchmark protocol as
pilot-ready. Generate that corpus outside this repository:

```bash
python3.11 scripts/generate_messy_benchmark_corpus.py \
  --target /tmp/noeticweave-messy-benchmark \
  --files 200
```

The generator creates:

| Artifact | Count |
| --- | ---: |
| Synthetic corpus files | 200 |
| Office-like `.docx` source files | 120 |
| Curated markdown notes | 80 |
| Plain conversion dump files | 120 |
| Benchmark tasks | 5 |
| Task/mode result slots | 15 |

It also writes `_meta/agent-readiness-tasks.yml`,
`_benchmark/plain_markitdown_dump/`, `_benchmark/agent-readiness-results-scaffold.yml`,
`_benchmark/messy-corpus-summary.json`, and `_benchmark/MESSY_BENCHMARK_RUN.md` in the generated
vault. `_benchmark/` is ignored by the NoeticWeave template because it may contain private run
worksheets and result scaffolds.

For a real external pilot, create the equivalent plain dump from the copied pilot vault with
`scripts/create_plain_markitdown_dump.py`; keep the resulting `_benchmark/` artifacts private.

For a reproducible synthetic dogfood score packet, generate the corpus with the reviewed-results
flag, then sync and validate the generated private result pack:

```bash
python3.11 scripts/generate_messy_benchmark_corpus.py \
  --target /tmp/noeticweave-messy-benchmark \
  --files 200 \
  --write-reviewed-results
noeticweave --root /tmp/noeticweave-messy-benchmark sync --json
noeticweave --root /tmp/noeticweave-messy-benchmark benchmark \
  --results _benchmark/agent-readiness-results-reviewed.yml \
  --require-results \
  --require-citations \
  --require-prompt-safety
```

Expected aggregate summary:

```text
raw_source_folder: results=5 score=3/10 avg=0.60 corrections=10 violations=0
plain_markitdown_dump: results=5 score=4/10 avg=0.80 corrections=8 violations=0
noeticweave_markdown: results=5 score=10/10 avg=2.00 corrections=0 violations=0
```

### Limits

- This is still synthetic dogfood evidence, not design-partner validation.
- The reviewed result pack contains scores, correction counts, prompt-safety flags, and path
  citations only; it does not contain answer text, reviewer notes, source bodies, or mirror bodies.
- Scores are intentionally conservative for raw-folder and plain-dump modes because update,
  audit, and consolidation tasks require manifest, lifecycle, generated-mirror, and curated-hub
  context.
- The next benchmark step is a real external design-partner run using the same task/result schema.
  That run is the evidence that can satisfy or fail the validation gate.
