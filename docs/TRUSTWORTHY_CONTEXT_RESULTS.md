# Trustworthy Context — deterministic benchmark results

Fixed pack: `tests/fixtures/trustworthy_context/pack.json`, 12 synthetic tasks, three collections,
three held-out tasks. Pack SHA-256: `ad9602e93d66e352b955a9ac2e4f3811d59dfa25ab80d89430a098f01e03839b`.
The manifest and initial baseline were captured before retrieval tuning. Query retrieval remains
opt-in. These are expected-source selection checks; they are not answer grades or citation-accuracy
measurements by a model. Source hashes, expected spans, prompts and budgets are in the manifest.

| Task | Split | Existing selection coverage | Query coverage | Insufficient-evidence empty selection (old → query) |
| --- | --- | --- | --- | --- |
| tc01 | development | 1.0 | 1.0 | — → — |
| tc02 | development | 0.0 | 1.0 | — → — |
| tc03 | held-out | 0.0 | 1.0 | — → — |
| tc04 | development | 1.0 | 1.0 | — → — |
| tc05 | development | 1.0 | 1.0 | — → — |
| tc06 | development | 0.0 | 1.0 | — → — |
| tc07 | held-out | 0.5 | 1.0 | — → — |
| tc08 | development | — | — | False → True |
| tc09 | development | 1.0 | 1.0 | — → — |
| tc10 | development | 0.0 | 1.0 | — → — |
| tc11 | held-out | 1.0 | 0.0 | — → — |
| tc12 | development | — | — | False → True |

Mean expected-source coverage across ten evidence-bearing tasks: **0.55 → 0.90**. Held-out mean
(three tasks): **0.50 → 0.67**. Held-out `tc11` regressed from 1.0 to 0.0 and is retained unchanged.
Both insufficient-evidence selections became empty. Empty selection is not measured model
abstention. This tiny pack does not establish statistical significance or general superiority.

Raw source and plain-conversion packets share the same sorted-source-order baseline and budgets;
code is registered through readable Markdown wrappers in the governed mode. This text pack does
not benchmark opaque Office/PDF extraction (see the separate bounded experiments). Two files and
4,000 estimated tokens are the common limits; serialized UTF-8 JSON bytes are measured and the
estimate is `ceil(bytes/4)`, not an actual model tokenizer count. Per-task latency, included spans,
bytes, selection reasons and omissions are in the raw JSON. Timing includes disposable setup and
must not be marketed as steady-state search latency.

Empirical evaluation is **PENDING endpoint/data/spend authorization**. No model calls or semantic
scores were fabricated. Correctness, citation accuracy, stale-evidence use, privacy/prompt-safety,
model abstention and human corrections remain null. The attack fixture tests selection boundaries;
it does not establish an agent's resistance to document instructions. The planned three stochastic
repeats have not run. Approval must identify endpoint/model/version, permitted data and maximum
spend, followed by human-calibrated scoring under the existing benchmark contract.

Reproduce locally with an installed wheel (outside the checkout):

```sh
mirrorarc benchmark --compact-pack /Users/cz/workspaces/cz1993/MirrorArc/tests/fixtures/trustworthy_context/pack.json --json > baseline.json
mirrorarc benchmark --compact-pack /Users/cz/workspaces/cz1993/MirrorArc/tests/fixtures/trustworthy_context/pack.json --task-retrieval --json > query.json
```

Measured final-wheel outputs: `/tmp/mirrorarc-tc-final/benchmark-baseline-final.json` and
`/tmp/mirrorarc-tc-final/benchmark-query-final.json`. Pre-tuning output:
`/tmp/mirrorarc-tc-benchmark-baseline.json`. Preserve these files for the planning review.
For an authorized model run, use the fixed prompt/task/source packets and the existing
[agent-readiness result protocol](AGENT_READINESS_BENCHMARK.md#compact-trustworthy-context-pack).
The benchmark intentionally has no endpoint-calling runner: authorization and an approved local
adapter are binding prerequisites, rather than credentials accepted implicitly by this package.
