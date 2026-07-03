# Agent-Readiness Benchmark Results

This page publishes aggregate benchmark evidence that is safe to keep in the public repository.
Private answer text, reviewer notes, source bodies, mirror bodies, and client-specific task packs
must stay outside this repo.

## 2026-07-03 Public Synthetic Dogfood

This is the first review-plan baseline run. It uses the public synthetic
`examples/government-services-vault` corpus and the task pack at
`examples/government-services-vault/_meta/agent-readiness-tasks.yml`.

It is **not external validation**. It is a dogfood run on a synthetic corpus so the project has a
published three-condition benchmark packet before design-partner work begins.

### Conditions

| Mode | Description |
| --- | --- |
| `raw_source_folder` | Original files and committed notes only. |
| `plain_markitdown_dump` | One-off Markdown conversion baseline without Vaultwright manifests, lifecycle state, or curated mirror workflow. |
| `vaultwright_markdown` | Vaultwright task context: source-linked curated notes plus generated mirror workflow and manifest/lifecycle semantics. |

### Aggregate Scores

| Mode | Results | Score | Average | Reviewer corrections | Privacy/provenance violations | Prompt-safety reviews |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `raw_source_folder` | 6 | 5 / 12 | 0.83 | 7 | 0 | 6 / 6 |
| `plain_markitdown_dump` | 6 | 6 / 12 | 1.00 | 6 | 0 | 6 / 6 |
| `vaultwright_markdown` | 6 | 12 / 12 | 2.00 | 0 | 0 | 6 / 6 |

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
python3.11 tools/vaultwright.py benchmark \
  --results _meta/public-agent-readiness-results.yml \
  --require-results \
  --require-citations \
  --require-prompt-safety
```

Expected summary:

```text
raw_source_folder: results=6 score=5/12 avg=0.83 corrections=7 violations=0
plain_markitdown_dump: results=6 score=6/12 avg=1.00 corrections=6 violations=0
vaultwright_markdown: results=6 score=12/12 avg=2.00 corrections=0 violations=0
```

### Limits

- This is synthetic dogfood evidence, not a design-partner result.
- Timing and token/tool-call counts were not captured in this packet.
- Generated mirror citations are omitted so the public result pack validates against the committed
  example tree without committing generated mirrors.
- The next benchmark step is a messy larger corpus and a real external design-partner run using
  the same task/result schema.
