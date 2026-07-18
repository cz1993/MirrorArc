# Stage 3 Validation Status

This is the public-safe status ledger for NoeticWeave's external validation gate. It tracks
design-partner attempts without naming participants, publishing source paths, or committing
private corpus, mirror, transcript, answer, or reviewer-note content.

Stage 3 is complete only when at least one permission-cleared external corpus has gone through the
package-owned pipeline and the evidence in `docs/VALIDATION_GATE.md` is recorded. Synthetic
dogfood runs, public examples, and generated benchmark corpora do not complete this gate.

## Current Status

As of 2026-07-03:

| Measure | Count | Notes |
| --- | ---: | --- |
| Accepted external pilot corpora | 0 | No external corpus has started the protocol. |
| Completed external pilot corpora | 0 | Stage 3 remains incomplete. |
| Second-sync self-service passes | 0 | Required before self-serve claims. |
| Second-sync self-service failures | 0 | Three failures trigger the service-workflow stop rule. |
| One-week return signals | 0 | Required for durable value evidence. |
| Publishable aggregate summaries | 0 | No external aggregate summary is public yet. |

## Profile Targets

| Profile shape | Target | Accepted | Completed | Status |
| --- | ---: | ---: | ---: | --- |
| `business-operations` | 1 | 0 | 0 | Matches the initial consulting wedge. |
| `research-learning` | 1 | 0 | 0 | Needed before claiming non-business profile readiness. |
| `software-project` | 1 | 0 | 0 | Needed for technical-documentation readiness. |

## Attempt States

Use these states when updating the public-safe attempt log:

- `invited`: outreach sent, no pre-screen yet;
- `pre_screened`: fit assessed, no corpus accepted yet;
- `accepted`: copied-corpus authority and boundaries are clear, first run scheduled;
- `deferred`: potentially useful but blocked by timing, data handling, or corpus shape;
- `rejected`: not a fit for the validation gate;
- `first_run_complete`: sandbox, doctor, sync, status, catalog, and review setup completed;
- `second_sync_pass`: participant ran the second sync without hands-on help;
- `second_sync_fail`: participant could not complete routine refresh without hands-on help;
- `follow_up_complete`: one-week return signal or clear stop reason recorded privately;
- `aggregate_published`: public-safe aggregate summary committed.

## Public Attempt Log

Record only anonymized, aggregate-safe fields here. Keep names, private paths, document titles,
source text, mirror text, answer text, reviewer notes, and transcripts in private pilot records.

| Attempt ID | Date | Profile shape | State | Corpus shape | Public-safe note |
| --- | --- | --- | --- | --- | --- |
| _No external attempts recorded yet._ |  |  |  |  |  |

## Update Rules

- Add one row per design-partner attempt using stable IDs such as `DP-001`.
- Describe corpus shape only as broad categories, such as `mixed Office/PDF, 50-200 files`.
- Use stop reason categories, not private explanations: `copy boundary`, `authority`, `timing`,
  `data restrictions`, `workflow mismatch`, `onboarding friction`, `second sync`, or
  `no return signal`.
- Link only to public-safe aggregate summaries, never to private worksheets or result packs.
- Update the current-status counts when an attempt changes state.
- Keep Stage 3 marked incomplete until the validation gate evidence is actually recorded.

## Private Evidence Location

Private pilot folders should contain the completed `docs/PILOT_WORKSHEET.md` copy, command
transcripts, result packs, and any participant feedback. Use
`docs/FIRST_EXTERNAL_PILOT_RUNBOOK.md` to prepare the first accepted run. This public repository
should contain only aggregate summaries that have passed a no-data review.
