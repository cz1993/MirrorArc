# NoeticWeave Validation Gate

This gate keeps NoeticWeave from expanding past the core mirror/catalog workflow before there is
evidence that the workflow is useful outside the maintainer's fixtures.

It applies before Stage 4 adapter work, Stage 5 index/exploration work, Stage 6 Explorer work, and
new connector or visualization tracks. Synthetic examples and dogfood packets can prepare the
protocol, but they do not complete this gate.

## Current Evidence

| Evidence packet | Status | Gate value |
| --- | --- | --- |
| Government-services synthetic benchmark | Complete | Proves the three-condition benchmark packet can distinguish raw folders, a plain markitdown dump, and NoeticWeave Markdown on a public synthetic corpus. |
| Messy 200-file synthetic benchmark | Complete | Proves the benchmark harness can generate and score a larger messy synthetic corpus without committing private run artifacts. |
| Permission-cleared external corpus | Not started | Required before Stage 3 is complete. |
| Independent design-partner return signal | Not started | Required before treating NoeticWeave as self-serve software. |

See `docs/STAGE3_VALIDATION_STATUS.md` for the public-safe attempt ledger. The status ledger does
not complete Stage 3 by itself; only protocol evidence from a permission-cleared external corpus
can do that.

## Benchmark Stop Rule

Every pilot benchmark must compare the same questions across:

- `raw_source_folder`;
- `plain_markitdown_dump`;
- `noeticweave_markdown`.

NoeticWeave shows meaningful advantage only when it is no worse than `plain_markitdown_dump` on
aggregate score and is better on at least two of these measures:

- reviewer correction count;
- citation/provenance validity;
- prompt-safety review completeness;
- operator ability to identify generated, stale, missing, or review-required material;
- time or tool calls needed to answer the fixed task set.

If an external benchmark packet shows no meaningful advantage over a plain markitdown dump, pivot
away from workspace-methodology expansion. The acceptable pivot is a narrower governed
materialization layer: manifests, lifecycle state, review ledgers, recovery, and integration
surfaces that help other tools consume authoritative source records. Do not keep adding
workspaces, adapters, indexes, or visual surfaces to compensate for weak benchmark evidence.

## Self-Service Stop Rule

The design-partner success metric is the second sync:

1. The participant receives or creates a copied, permission-cleared vault.
2. The participant runs the first sync and reviews the catalog/front door with support.
3. The participant changes or moves selected source files.
4. The participant runs the second sync without hands-on help.
5. The participant confirms the lifecycle/status output did not introduce unexpected regressions.

If three design-partner attempts fail at the second-sync gate, treat NoeticWeave as an
operator-run service workflow before treating it as self-serve software. The product can still be
valuable, but the next work should be packaging the service workflow, support protocol, and private
handoff artifacts rather than broadening the public CLI.

## Expansion Gate

Do not start these tracks until Stage 3 external evidence is recorded:

- richer Obsidian adapter or skill installation work;
- generated Canvas or profile-specific presentation presets beyond the current `.base` path;
- local evidence index, exploration CLI, MCP exploration tool, or visual Explorer;
- Docling, email, Teams, SharePoint, or other connector adapters;
- new visualization surfaces.

After Stage 3, each expansion still needs its own measured reason. The index and Explorer remain
conditional on benchmark evidence that they materially improve context precision, citation
quality, reviewer correction effort, tool-call count, or operator handoff compared with the core
mirror/catalog workflow.

## Evidence Handling

External gate evidence must stay out of this public repository unless it is synthetic or
permission-cleared public data. Store only aggregate public summaries here:

- corpus shape, not source or mirror bodies;
- command transcript with sensitive paths redacted;
- benchmark aggregate scores and validation output;
- review-ledger counts, not review text tied to private content;
- conversion, recovery, catalog, Microsoft 365 handoff, and pilot summaries that omit source text;
- participant quotes only with written permission.

Useful gate commands include:

```bash
noeticweave --root "$VW" sandbox --source-root /path/to/original-copy-source
noeticweave --root "$VW" sync --json
noeticweave --root "$VW" status --json
noeticweave --root "$VW" doctor --json
noeticweave --root "$VW" catalog
noeticweave --root "$VW" catalog --html
noeticweave --root "$VW" conversion --guide
noeticweave --root "$VW" recovery --worksheet
python3.11 /path/to/noeticweave/scripts/create_plain_markitdown_dump.py --root "$VW" --force
noeticweave --root "$VW" benchmark --results _meta/agent-readiness-results.yml --require-results --require-citations --require-prompt-safety
noeticweave --root "$VW" pilot --json
noeticweave --root "$VW" pilot --worksheet
```

Full sync remains the recovery and verification path. Journaled changed-file materialization is
the normal steady-state path, but filesystem and Office events are observations, not authoritative
transactions.
