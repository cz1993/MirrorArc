# Pilot Worksheet

Use this worksheet for a permission-cleared design-partner pilot. Keep completed worksheets and
command transcripts outside this public repository unless every source is synthetic or public-domain
and the owner has approved publication.

For the first accepted external run, follow `docs/FIRST_EXTERNAL_PILOT_RUNBOOK.md` and use this
worksheet as the private record.

## Pilot Setup

- Participant/team:
- Operator:
- Recruiting source:
- Profile shape:
- Pre-screen outcome:
- Date range:
- Corpus boundary:
- Source copy location:
- Pilot vault path (`VW`):
- Original source root used for sandbox preflight:
- Cloud AI providers used, if any:
- Data handling constraints:

## Baseline

- Current document-review workflow:
- Main pain points:
- Current tools:
- Security or workspace-boundary constraints:
- Baseline time to answer the fixed question set:

## Corpus Shape

Record from `python3.11 tools/vaultwright.py pilot --json` after first sync:

- content file count:
- total content bytes:
- Office/PDF source candidates:
- source manifest records:
- source formats:
- repo manifest records:
- sync audit event count:
- conversion high/medium/low counts:
- conversion-quality result records:
- conversion-quality reviewed records:
- conversion-quality missing reviews:
- conversion-quality average score:
- conversion-quality issue-code counts:
- conversion-quality correction count:
- recovery action count:
- overlap current candidate count:
- overlap near-miss count:
- overlap comparable pair count:
- overlap thresholds:
- review-ledger reviewed artifacts:
- review-ledger stale/missing or non-approved decisions:
- benchmark task count:
- benchmark result count:
- benchmark missing task/mode scores:

Do not paste source paths, document text, mirror text, secrets, personal data, or protected identifiers
into this worksheet.

For a paste-ready aggregate summary, use:

```bash
python3.11 tools/vaultwright.py pilot --worksheet
```

This prints a Markdown summary with counts, review queues, and private worksheet prompts. It omits
source paths, source text, mirror text, answer text, reviewer notes, and protected identifiers.

## Run Log

Record command results and elapsed time. Use the installed package command when possible:

```bash
export VW="/path/to/copied-pilot-vault"
vaultwright --root "$VW" sandbox --source-root /path/to/original-documents
vaultwright --root "$VW" doctor
vaultwright --root "$VW" doctor --json
vaultwright --root "$VW" plan
vaultwright --root "$VW" sync
vaultwright --root "$VW" sync --json
vaultwright --root "$VW" status
vaultwright --root "$VW" status --json
vaultwright --root "$VW" catalog
vaultwright --root "$VW" catalog --html
vaultwright --root "$VW" conversion --guide
vaultwright --root "$VW" conversion --init-results
vaultwright --root "$VW" conversion --results _meta/conversion-quality-results.yml --require-reviewed # after filling scaffold
vaultwright --root "$VW" recovery
vaultwright --root "$VW" overlap
vaultwright --root "$VW" overlap --worksheet
vaultwright --root "$VW" m365
vaultwright --root "$VW" review --json
vaultwright --root "$VW" benchmark --init-tasks
vaultwright --root "$VW" benchmark --worksheet
vaultwright --root "$VW" benchmark --require-generated
vaultwright --root "$VW" benchmark --init-results
vaultwright --root "$VW" benchmark \
  --results _meta/agent-readiness-results.yml \
  --require-results \
  --require-citations \
  --require-prompt-safety
vaultwright --root "$VW" pilot --json
vaultwright --root "$VW" pilot --worksheet
vaultwright --root "$VW" lint
```

If the installed command is not available, run the same commands from inside the copied vault with
`python3.11 tools/vaultwright.py`.

## Review Results

- Unsupported/skipped files:
- Conversion high-priority items reviewed:
- Conversion medium-priority spot checks reviewed:
- Conversion guide checklist completed:
- Conversion-quality result pack completed:
- Conversion-quality average score:
- Conversion-quality correction count:
- Conversion-quality issue-code counts:
- Recovery items resolved:
- Overlap candidates reviewed:
- Overlap near misses spot-checked:
- Review ledger current approvals:
- Review ledger stale or non-approved items:
- Manual corrections made:
- Prompt-safety reviewed result count:
- Prompt-safety violation count:
- Prompt-safety missing review count:
- Overlap threshold changes from `_meta/lint-config.yml`:
- Curated hubs/entity pages created:
- Source files verified unchanged:
- Second sync idempotency result:

## Agent-Readiness Tasks

Use `docs/AGENT_READINESS_BENCHMARK.md` for scoring. Keep prompts, scores, and citations
anonymized, and keep any private result pack outside this public repository unless it has been
reviewed for source text, personal data, protected names, answer text, and reviewer notes.

| Task ID | Raw folder score | Plain markitdown dump score | Vaultwright markdown score | Prompt safety reviewed? | Notes |
| --- | ---: | ---: | ---: | --- | --- |
| | | | | | |

## Success Matrix

| Gate | Evidence captured | Pass? | Follow-up |
| --- | --- | --- | --- |
| Copy-boundary preflight completed before first sync | | | |
| First sync, status, catalog, and HTML catalog completed | | | |
| High-priority conversion/recovery blockers resolved or documented | | | |
| Agent-readiness result pack passes strict result, citation, and prompt-safety validation | | | |
| Participant reran sync without help and no unexpected lifecycle regressions appeared | | | |
| Participant returned within one week or gave a clear stop reason | | | |

## Outcome

- Time to answer fixed questions before Vaultwright:
- Time to answer fixed questions after Vaultwright:
- Operator confidence score:
- Support time required:
- Participant ran second sync without help:
- Participant returned after one week:
- Issues found:
- Product changes requested:
- Publishable quote, only with written permission:

## Decision

- Continue pilot:
- Stop reason, if applicable:
- Next product fix:
- Next validation corpus:
