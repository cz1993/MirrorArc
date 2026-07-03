# Design Partner Recruiting

Vaultwright's next validation work is not another adapter, index, or visualization surface. It is
finding a small number of external operators who can test the core mirror/catalog workflow on
permission-cleared, real client-shaped corpora.

Use this packet before `docs/DESIGN_PARTNER_PROTOCOL.md`. It turns the review-plan requirement
for 2-3 design partners into a repeatable recruiting, screening, and scheduling flow. Record
public-safe attempt state in `docs/STAGE3_VALIDATION_STATUS.md`.

## Recruiting Goal

Recruit three independent design partners if possible:

- one consulting, advisory, implementation, compliance, or operations team using the
  `business-operations` profile shape;
- one research, grant, education, policy, or learning-heavy operator using the
  `research-learning` profile shape;
- one small software, documentation, or technical delivery team using the `software-project`
  profile shape.

The first accepted external corpus can satisfy the Stage 3 "first real corpus" gate only after it
passes the protocol evidence requirements. All three profile pilots are still needed before
claiming broad v0.1 readiness.

## Good-Fit Signals

Prioritize teams that:

- receive messy document collections repeatedly;
- already need provenance, review status, or handoff evidence;
- can legally make a local duplicate of one bounded corpus;
- have 50 to 2,000 files in one engagement or protected boundary;
- can spare one operator for setup, first sync, second sync, and one-week follow-up;
- are willing to compare raw-folder, plain-dump, and Vaultwright-Markdown task answers;
- will say what failed, not only what looked promising.

Defer teams that:

- need hosted multi-user storage before local validation;
- cannot duplicate or process the corpus locally;
- require legal, tax, accounting, medical, or compliance conclusions from Vaultwright;
- expect Vaultwright to mutate original source files;
- want mailbox, SharePoint, Teams, Docling, MCP, Explorer, or vector-RAG work before proving the
  core mirror/catalog workflow.

## Pre-Screen Checklist

Use a 15-20 minute pre-screen before accepting a pilot:

- What recurring document workflow is painful today?
- What source systems and file types are in the candidate corpus?
- Roughly how many files and how much data are in the bounded corpus?
- Who has authority to duplicate and process the corpus locally?
- Are there secrets, credentials, regulated personal data, or contractual restrictions?
- Can the participant use a copied vault outside the original source root?
- Can the participant run an installed command, or will the operator run commands during a screen
  share?
- What fixed questions or updates would prove value?
- Can the participant modify or move selected copied sources and run the second sync without
  hands-on help?
- Will the participant join a one-week follow-up or give a clear stop reason?

Accept only when the answer to the copy-boundary and authority questions is clear. If the data
handling answer is uncertain, do not start a pilot.

## Acceptance Checklist

Before scheduling the first run, record privately:

- participant/team and operator;
- profile shape to test;
- corpus boundary and source owner;
- source copy location;
- planned pilot vault path;
- allowed tools and cloud AI providers;
- explicit exclusions, such as secrets, HR files, financial account data, protected health data,
  customer personal data, or privileged legal material;
- fixed question set and expected citations;
- second-sync scenario;
- one-week follow-up date.

Do not record private names, source paths, document text, mirror text, answer text, or reviewer
notes in this public repository.

## Pilot Cadence

- Pre-screen, 15-20 minutes: accept, defer, or reject before any source copy.
- Prep, 30-60 minutes: create copied corpus and copied vault; confirm local boundary and backup
  posture.
- First run, 60-90 minutes: run sandbox, doctor, plan, sync, status, catalog, conversion,
  recovery, and benchmark setup.
- Second sync, 15-30 minutes: participant changes or moves copied sources, then runs sync without
  hands-on help.
- Follow-up, one week later: confirm return signal, stop reason, and whether the workflow was
  tangible enough.

## Stop Conditions

Stop or defer the pilot when:

- the corpus cannot be copied safely;
- the copied vault is the original source root;
- the participant is not authorized to process the data locally;
- the pilot would require committing private source, mirror, result-pack, or transcript content;
- setup requires building a gated Phase 2 feature first;
- the participant cannot attempt the second sync;
- the workflow has no clear fixed questions or success signal.

## Outreach Templates

### Initial Ask

```text
Hi [name],

I am looking for 2-3 design partners for Vaultwright, a local tool that turns a copied document
collection into a governed Markdown workspace without changing the original files.

The current test is narrow: can a consulting/advisory/operations-style team get clearer inventory,
source-linked Markdown, review status, and agent-readable context from a real copied corpus than
from raw folders or a plain one-time Markdown dump?

The pilot would use a permission-cleared copy of one bounded corpus, not production originals. We
would run the first sync together, compare a fixed question set across raw folder, plain dump, and
Vaultwright Markdown, then ask you to run a second sync after changing or moving a few copied
source files.

No private files, mirror bodies, answer text, or source paths would be published. I would only keep
aggregate counts and your feedback unless you explicitly approve a quote.

Would you be open to a 15-minute pre-screen to see whether your workflow is a fit?
```

### Follow-Up

```text
Hi [name],

Quick follow-up on the Vaultwright design-partner pilot. The best-fit workflow is a messy but
bounded document collection where provenance, refresh, review status, or handoff is currently
painful.

If the corpus cannot be copied locally or the timing is not right, no worries. A clear "not now" is
useful signal too.
```

### Confirmation

```text
Thanks for agreeing to pre-screen Vaultwright.

Before we touch any files, we will confirm:

- the corpus can be duplicated locally;
- the copied vault is not the original source root;
- no secrets or restricted material are included;
- which cloud AI providers, if any, are allowed;
- the fixed questions that would prove value;
- the second-sync scenario you will run without hands-on help.

If any of those are unclear, we will defer the pilot rather than force it.
```

### Deferral

```text
Thanks for walking through the workflow. I do not think this is the right pilot corpus yet because
[reason].

The safest next step is [copy-boundary cleanup / smaller corpus / different workflow / revisit
later]. I would rather defer than create a data-handling or expectation problem.
```

## Private Record Template

Keep this in the private pilot folder, not in the public repository:

```text
Participant:
Profile shape:
Accepted / deferred / rejected:
Reason:
Corpus boundary:
Authority to copy:
Data exclusions:
Allowed tools/providers:
Fixed questions:
Second-sync scenario:
Scheduled first run:
Scheduled follow-up:
```

After each pre-screen, update `docs/STAGE3_VALIDATION_STATUS.md` with only anonymized attempt
state and broad corpus shape.

When an attempt reaches `accepted`, use `docs/FIRST_EXTERNAL_PILOT_RUNBOOK.md` to prepare the
first run.
