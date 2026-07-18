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

Record from `noeticweave --root "$VW" pilot --json` after first sync:

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
noeticweave --root "$VW" pilot --worksheet
```

This prints a Markdown summary with counts, review queues, and private worksheet prompts. It omits
source paths, source text, mirror text, answer text, reviewer notes, and protected identifiers.

## Run Log

Record command results and elapsed time. Use the installed package command when possible:

```bash
export VW="/path/to/copied-pilot-vault"
noeticweave --version
noeticweave profile list
noeticweave --root "$VW" sandbox --source-root /path/to/original-documents
noeticweave --root "$VW" doctor
noeticweave --root "$VW" doctor --json
noeticweave --root "$VW" plan
noeticweave --root "$VW" sync
noeticweave --root "$VW" sync --json
noeticweave --root "$VW" status
noeticweave --root "$VW" status --json
noeticweave --root "$VW" catalog
noeticweave --root "$VW" catalog --html
noeticweave --root "$VW" conversion --guide
noeticweave --root "$VW" conversion --init-results
noeticweave --root "$VW" conversion --results _meta/conversion-quality-results.yml --require-reviewed # after filling scaffold
noeticweave --root "$VW" recovery
noeticweave --root "$VW" overlap
noeticweave --root "$VW" overlap --worksheet
noeticweave --root "$VW" m365
noeticweave --root "$VW" review --json
python3.11 /path/to/noeticweave/scripts/create_plain_markitdown_dump.py --root "$VW" --force
noeticweave --root "$VW" benchmark --init-tasks
noeticweave --root "$VW" benchmark --worksheet
noeticweave --root "$VW" benchmark --require-generated
noeticweave --root "$VW" benchmark --init-results
noeticweave --root "$VW" benchmark \
  --results _meta/agent-readiness-results.yml \
  --require-results \
  --require-citations \
  --require-prompt-safety
noeticweave --root "$VW" pilot --json
noeticweave --root "$VW" pilot --worksheet
noeticweave --root "$VW" lint
```

If the installed command is not available, run the same commands from inside the copied vault with
`python3.11 tools/noeticweave.py`.

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

| Task ID | Raw folder score | Plain markitdown dump score | NoeticWeave markdown score | Prompt safety reviewed? | Notes |
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

- Time to answer fixed questions before NoeticWeave:
- Time to answer fixed questions after NoeticWeave:
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
