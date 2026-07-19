# First External Pilot Runbook

Use this runbook only after a design partner has passed the recruiting pre-screen in
`docs/DESIGN_PARTNER_RECRUITING.md`. It turns the accepted pilot into a controlled first run
without adding a new product surface or weakening the Stage 3 gate.

This runbook is public-safe. Completed worksheets, command transcripts, result packs, source
paths, mirror paths, answer text, reviewer notes, and participant feedback belong in the private
pilot folder, not in this repository.

## Preconditions

Do not start the first run until all of these are true:

- the participant has authority to duplicate and process the bounded corpus locally;
- the original source collection is not the pilot vault;
- the copied pilot vault is outside this public source repository;
- secrets, credentials, protected personal data, privileged material, and excluded folders have
  been removed or explicitly ruled out;
- the participant has chosen a profile shape;
- the fixed question set and second-sync scenario are known;
- the private evidence folder exists outside the public repository;
- `docs/STAGE3_VALIDATION_STATUS.md` has an anonymized attempt row in `accepted` state.

If any precondition is uncertain, defer the pilot rather than improvising during the call.

## Private Setup

Prepare private paths before the call:

```bash
export VW="/path/to/copied-pilot-vault"
export ORIGINAL_ROOT="/path/to/original-source-root"
export PRIVATE_EVIDENCE="/path/to/private-pilot-evidence/DP-001"
mkdir -p "$PRIVATE_EVIDENCE"
```

Keep `PRIVATE_EVIDENCE` out of this repository. It may contain command output, local paths,
private result packs, and completed worksheet copies.

Copy the public worksheet into the private evidence folder:

```bash
cp docs/PILOT_WORKSHEET.md "$PRIVATE_EVIDENCE/PILOT_WORKSHEET.md"
```

## Operator Environment Smoke Test

Before the participant is on the call, confirm the installed command is the one the runbook will
use:

```bash
command -v mirrorarc
mirrorarc --version
mirrorarc profile list
```

If the installed command is unavailable, either install MirrorArc with the package-first
`uvx`/`pipx` path from `docs/quickstart.md` or plan to use the copied vault's compatibility wrapper
explicitly. Do not spend participant time debugging Python packaging.

## First-Run Sequence

Run commands with the installed package when possible. If the installed command is unavailable,
use the copied vault's compatibility wrapper as described in `docs/PILOT_WORKSHEET.md`.

### 1. Boundary And Readiness

```bash
mirrorarc --root "$VW" sandbox --source-root "$ORIGINAL_ROOT" \
  > "$PRIVATE_EVIDENCE/01_sandbox.txt"
mirrorarc --root "$VW" doctor --json \
  > "$PRIVATE_EVIDENCE/02_doctor.json"
mirrorarc --root "$VW" plan \
  > "$PRIVATE_EVIDENCE/03_plan.txt"
mirrorarc --root "$VW" status --json \
  > "$PRIVATE_EVIDENCE/04_status_before_sync.json"
```

Stop before sync if sandbox or doctor reports unresolved copy-boundary, backup, profile,
lifecycle, tool, or dependency errors.

### 2. First Sync And Front Door

```bash
mirrorarc --root "$VW" sync --json \
  > "$PRIVATE_EVIDENCE/05_sync.json"
mirrorarc --root "$VW" status --json \
  > "$PRIVATE_EVIDENCE/06_status_after_sync.json"
mirrorarc --root "$VW" catalog \
  > "$PRIVATE_EVIDENCE/07_catalog.txt"
mirrorarc --root "$VW" catalog --html --stdout \
  > "$PRIVATE_EVIDENCE/08_catalog.html"
```

Stop or narrow the pilot if unsupported, conflicted, missing, error, or review-required states
block the participant's first workflow.

### 3. Conversion, Recovery, And Review

```bash
mirrorarc --root "$VW" conversion --guide \
  > "$PRIVATE_EVIDENCE/09_conversion_guide.txt"
mirrorarc --root "$VW" recovery --worksheet \
  > "$PRIVATE_EVIDENCE/10_recovery_worksheet.md"
mirrorarc --root "$VW" review --json \
  > "$PRIVATE_EVIDENCE/11_review.json"
```

The operator and participant should spot-check high-priority conversion and recovery items before
using generated mirrors for source-backed decisions.

### 4. Benchmark Setup

Create the plain conversion baseline in the copied pilot vault before scoring. This is the
`plain_markitdown_dump` comparison mode required by `docs/VALIDATION_GATE.md`:

```bash
python3.11 /path/to/mirrorarc/scripts/create_plain_markitdown_dump.py \
  --root "$VW" \
  --force \
  > "$PRIVATE_EVIDENCE/12_plain_markitdown_dump.txt"
```

The dump lives under `$VW/_benchmark/plain_markitdown_dump/`. Treat it as private pilot evidence:
it may contain source-derived text and private relative paths.

```bash
mirrorarc --root "$VW" benchmark --init-tasks
mirrorarc --root "$VW" benchmark --worksheet \
  > "$PRIVATE_EVIDENCE/13_benchmark_worksheet.md"
mirrorarc --root "$VW" benchmark --init-results
```

Edit the task and result packs privately. The three comparison modes must remain:

- `raw_source_folder`;
- `plain_markitdown_dump`;
- `mirrorarc_markdown`.

Validate the private result pack after scoring:

```bash
mirrorarc --root "$VW" benchmark \
  --results _meta/agent-readiness-results.yml \
  --require-results \
  --require-citations \
  --require-prompt-safety \
  > "$PRIVATE_EVIDENCE/14_benchmark_validation.txt"
```

Stop the benchmark claim if scored answers lack citations or prompt-safety review.

### 5. Aggregate Private Evidence

```bash
mirrorarc --root "$VW" pilot --json \
  > "$PRIVATE_EVIDENCE/15_pilot.json"
mirrorarc --root "$VW" pilot --worksheet \
  > "$PRIVATE_EVIDENCE/16_pilot_worksheet.md"
mirrorarc --root "$VW" lint \
  > "$PRIVATE_EVIDENCE/17_lint.txt"
```

Use the aggregate output to complete the private worksheet. Do not copy private result packs,
transcripts, source paths, mirror bodies, answer text, or reviewer notes into this repository.

## Second-Sync Sequence

Before the call ends, choose a small copied-source change that the participant understands:

- edit one copied Office/PDF/text source;
- move one copied source within the same protected boundary; or
- remove one copied source that is safe to mark missing.

Then ask the participant to run the refresh without hands-on help:

```bash
mirrorarc --root "$VW" sync --changed --json \
  > "$PRIVATE_EVIDENCE/18_second_sync_changed.json"
mirrorarc --root "$VW" status --json \
  > "$PRIVATE_EVIDENCE/19_status_after_second_sync.json"
```

If changed-file sync is not appropriate for the pilot vault, use the full recovery path instead:

```bash
mirrorarc --root "$VW" sync --full --json \
  > "$PRIVATE_EVIDENCE/18_second_sync_full.json"
```

Record `second_sync_pass` only when the participant completes routine refresh without hands-on
help and no unexpected lifecycle regression appears.

## Follow-Up

Schedule the follow-up before ending the first run. One week later, record privately:

- whether the participant returned to the vault;
- which workflow, if any, they tried without the operator;
- whether the catalog or mirrors were tangible without Obsidian;
- what confused them;
- whether the next pilot should continue, narrow, or stop.

Update `docs/STAGE3_VALIDATION_STATUS.md` only with anonymized public-safe state changes and broad
corpus shape.

## Public-Safe Publication

Publish only after a no-data review. A public aggregate summary may include:

- profile shape;
- broad corpus size and file categories;
- benchmark aggregate scores;
- second-sync pass/fail count;
- one-week return signal;
- stop reason category;
- product fixes made.

It must not include private names, organizations, source paths, source text, mirror text, answer
text, reviewer notes, transcripts, or private result packs.
