# Vaultwright Validation Gate

This gate keeps Vaultwright from expanding past the core mirror/catalog workflow before there is
evidence that the workflow is useful outside the maintainer's fixtures.

It applies before Stage 4 adapter work, Stage 5 index/exploration work, Stage 6 indexed Explorer
work, and new connector or visualization tracks. One explicit exception is allowed: the implemented
bounded Stage 3 Guided Knowledge Map/Navigator slice described below may be used and corrected as
an orientation and comprehension test instrument. Synthetic examples and dogfood packets can
prepare the protocol, but they do not complete this gate.

## Current Evidence

| Evidence packet | Status | Gate value |
| --- | --- | --- |
| Government-services synthetic benchmark | Complete | Proves the three-condition benchmark packet can distinguish raw folders, a plain markitdown dump, and Vaultwright Markdown on a public synthetic corpus. |
| Messy 200-file synthetic benchmark | Complete | Proves the benchmark harness can generate and score a larger messy synthetic corpus without committing private run artifacts. |
| Permission-cleared external corpus | Not started | Required before Stage 3 is complete. |
| Independent design-partner return signal | Not started | Required before treating Vaultwright as self-serve software. |

See `docs/STAGE3_VALIDATION_STATUS.md` for the public-safe attempt ledger. The status ledger does
not complete Stage 3 by itself; only protocol evidence from a permission-cleared external corpus
can do that.

## Benchmark Stop Rule

Every pilot benchmark must compare the same questions across:

- `raw_source_folder`;
- `plain_markitdown_dump`;
- `vaultwright_markdown`.

Vaultwright shows meaningful advantage only when it is no worse than `plain_markitdown_dump` on
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

If three design-partner attempts fail at the second-sync gate, treat Vaultwright as an
operator-run service workflow before treating it as self-serve software. The product can still be
valuable, but the next work should be packaging the service workflow, support protocol, and private
handoff artifacts rather than broadening the public CLI.

## Bounded Stage 3 Navigator Proof

The Guided Knowledge Map/Navigator may proceed before Stage 3 external evidence is complete only
inside all of these boundaries:

- scan allowed Markdown, profile metadata, manifests, lifecycle/review metadata, headings, and
  explicit links when the UI opens or the user explicitly rescans;
- keep the scan model ephemeral and in memory;
- bind to localhost and serve a read-only Start/Map/Reader/Trail experience; the implemented Map is
  an ephemeral interactive HTML Canvas capped to the selected document's one-hop neighborhood,
  with complete inbound/outbound list equivalents, not a generated Obsidian `.canvas` artifact;
- use curated `_meta/navigation.yml` trails, safe profile landmarks, and bounded explicit-link
  neighborhoods;
- persist no document bodies, excerpts, document paths, trail state, recent-file history, search
  index, or shadow graph in browser URLs, local storage, or workspace files;
- add no SQLite/FTS index, embeddings, semantic ranking, MCP exploration, background watcher,
  unfiltered global graph, remote service, telemetry, or CDN assets;
- write nothing to the workspace and expose no UI-only lifecycle or authority logic;
- generate a new unguessable token for each launch, require it on the initial launch URL or API
  header, and scrub it from browser history after bootstrap; require the exact loopback `Host`,
  reject mismatched `Origin` and `Sec-Fetch-Site: cross-site`, and preserve path containment,
  symlink, private-root, XSS/active-content, prompt-safety, accessibility, and aggregate-only
  logging controls;
- label it **Navigator**, not **Explorer**.

This exception exists because the first external pilot needs a credible non-Obsidian front door to
compare against the catalog. It does not authorize a general visualization track and does not
count as Stage 3 progress by itself. `docs/STAGE3_VALIDATION_STATUS.md` remains authoritative for
accepted/completed external-corpus counts.

The bounded software slice and its synthetic safety tests are implemented. That changes readiness
to run the comparison, not the gate status: the permission-cleared external corpus and independent
return signal above are still `Not started`, so Stage 3 remains incomplete.

For the same fixed orientation and comprehension tasks, compare ordinary Markdown/catalog use
with Navigator. Record only aggregate-safe measures:

- time to first useful document;
- successful start selection without coaching;
- wrong turns and backtracks;
- trail completion and supporting-link return;
- fixed comprehension-question accuracy;
- source-authority, provenance, lifecycle, and review-warning recognition;
- documents opened, navigation actions, reviewer corrections, and task time;
- keyboard-only completion and automated accessibility violations;
- scan time, peak memory, document/link counts, and rejected-path counts.

The proof may continue toward v1 only when a permission-cleared external run shows no safety
regression and a meaningful improvement over the catalog on at least two primary measures: time
to first useful document, wrong turns, comprehension, provenance/lifecycle recognition, or
reviewer correction count. If it is mainly aesthetic, duplicates the catalog, needs extensive
coaching, or obscures trust state, remove it from the v1 critical path.

## Expansion Gate

Do not start these tracks until Stage 3 external evidence is recorded:

- richer Obsidian adapter or skill installation work;
- generated Obsidian `.canvas` or profile-specific presentation presets beyond the current `.base`
  path;
- local evidence index, exploration CLI, MCP exploration tool, or indexed visual Explorer;
- Docling, email, Teams, SharePoint, or other connector adapters;
- new visualization surfaces beyond the bounded Navigator proof above.

After Stage 3, each expansion still needs its own measured reason. The index and Explorer remain
conditional on benchmark evidence that they materially improve context precision, citation
quality, reviewer correction effort, tool-call count, or operator handoff compared with the core
mirror/catalog/Navigator workflow. Navigator may later become an Explorer mode, but it cannot
smuggle corpus-wide retrieval into Stage 3.

## Evidence Handling

External gate evidence must stay out of this public repository unless it is synthetic or
permission-cleared public data. Store only aggregate public summaries here:

- corpus shape, not source or mirror bodies;
- command transcript with sensitive paths redacted;
- benchmark aggregate scores and validation output;
- review-ledger counts, not review text tied to private content;
- conversion, recovery, catalog, Microsoft 365 handoff, and pilot summaries that omit source text;
- Navigator task timings, action counts, comprehension/trust scores, scan counts, and rejected-path
  counts without document titles, paths, headings, bodies, or participant identity;
- participant quotes only with written permission.

Useful gate commands include:

```bash
vaultwright --root "$VW" sandbox --source-root /path/to/original-copy-source
vaultwright --root "$VW" sync --json
vaultwright --root "$VW" status --json
vaultwright --root "$VW" doctor --json
vaultwright --root "$VW" catalog
vaultwright --root "$VW" catalog --html
vaultwright --root "$VW" conversion --guide
vaultwright --root "$VW" recovery --worksheet
python3.11 /path/to/vaultwright/scripts/create_plain_markitdown_dump.py --root "$VW" --force
vaultwright --root "$VW" benchmark --results _meta/agent-readiness-results.yml --require-results --require-citations --require-prompt-safety
vaultwright --root "$VW" pilot --json
vaultwright --root "$VW" pilot --worksheet
```

Full sync remains the recovery and verification path. Journaled changed-file materialization is
the normal steady-state path, but filesystem and Office events are observations, not authoritative
transactions.
