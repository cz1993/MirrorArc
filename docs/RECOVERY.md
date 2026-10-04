# Recovery Guide

## Purpose

MirrorArc must be recoverable because it works near authoritative business records. Recovery
procedures preserve the core promise: source files stay untouched, generated mirrors can be
regenerated, derived relationship/view/context state can be rebuilt, and authoritative or reviewed
Markdown can be restored from versioned backups.

## What To Back Up

Back up the whole vault before first sync and before bulk changes:

- original source folders;
- authoritative Markdown records and governed reviewed-view artifacts;
- `_meta/source-manifest.json`;
- `_meta/repo-manifest.json`;
- `_meta/sync-audit.jsonl`;
- `log.md`;
- `tools/repos.yml`;
- `.mirrorarc/state.sqlite` and any SQLite journal sidecars;
- `_meta/knowledge-views/`, `_meta/review-ledger.jsonl`, and persisted context definitions;
- frozen evidence under `.mirrorarc/cache/context/` and historical answer candidates under
  `.mirrorarc/cache/pageindex/<source-id>/answers/` when retaining an audit trail;
- `.obsidian/` settings only if the operator intentionally versions them.

Do not back up secrets into the vault. Keep tokens in the OS keychain or environment.
Hidden directories are part of the backup. A folder named `cache` is not a promise that every
file inside it can be recreated: a model answer and its exact frozen evidence are historical
records, even though neither becomes source authority.

Stop watchers, scheduled syncs and other writers before taking a whole-vault filesystem copy.
Close their database connections and checkpoint SQLite before copying; do not copy only the main
database from a running vault and omit its journal. If writers cannot be stopped, use a
SQLite-consistent backup procedure and coordinate it with the source/artifact snapshot. This guide's
local drill covers a quiescent vault, not a live multi-writer or cloud-sync snapshot.

## Restore a whole vault

1. Preserve the damaged vault separately. Do not restore over an active workspace or writer.
2. Copy the complete backup, including hidden state and audit evidence, into a new local folder.
3. Compare the restored file inventory and SHA-256 hashes with the backup before running tools.
4. Use the same validated MirrorArc and optional-provider versions. Reconfigure credentials
   outside the vault; do not copy secrets into the backup.
5. Run `mirrorarc --root /absolute/path/to/restored-vault recovery --json`, then inspect
   `relationships export`, `view status --json`, `context status --json` and `document status --json`.
   Compare saved review decisions and source/frozen hashes with the backup, not only counts.
6. Resolve reported conflicts before sync. Run lint and regenerate the Catalog before resuming
   normal work. A previously saved Catalog is a snapshot, not a live recovery check.

The October 3 local installed-wheel drill restored 84 synthetic-vault files at a new path with
identical hashes. It preserved a reviewed view, six frozen packs, one scripted historical answer
candidate and an accepted synthetic relationship-review decision. Those fixtures are not human
acceptance of a release. Repeat the drill for the operator's actual storage and backup system.

## Copied-Vault Sandbox Preflight

Before piloting on a real document collection, duplicate the source collection and run MirrorArc
only in the copied vault. Then run the read-only sandbox report:

```bash
python3.11 tools/mirrorarc.py sandbox --source-root /path/to/original-documents
python3.11 tools/mirrorarc.py sandbox --source-root /path/to/original-documents --json
```

The report verifies that the pilot vault is not the same path as the original source root, checks
required MirrorArc files/tools, counts source candidates, flags generated source mirrors sitting
outside `_mirrors/`, summarizes manifest/audit/recovery readiness, and checks basic git backup
posture. It does not print source paths, document text, mirror text, or repository document bodies.
Treat sandbox errors as blockers before the first sync. Treat warnings as review items to resolve
or explicitly accept in the private pilot worksheet.

## Regenerate Generated Mirrors

After verifying the whole-vault backup, identify generated mirror paths in the source and repo
manifests. Move only those generated artifacts to a separately named recovery folder outside the
vault; preserve annotations and reviewed Markdown first. Do not use a blanket deletion of source
folders or assume a hard-coded repository-note directory is correct for the current profile.
Then rebuild from the original sources:

```bash
python3.11 tools/mirrorarc.py plan
python3.11 tools/mirrorarc.py sync
python3.11 tools/mirrorarc.py status
python3.11 tools/mirrorarc.py lint
```

Review the plan before sync if the source tree changed, especially after folder renames or cloud
sync conflicts.

Full sync remains the authoritative recovery mode after Stage 1B. If journal state is lost or
suspect, stop any watcher, preserve the database, and rebuild operational state from sources and
manifests through reconciliation or full sync. The journal is not source authority, but the shared
database also contains review decisions that must not be discarded as disposable cache.

The same `.mirrorarc/state.sqlite` boundary owns relationship, dependency, L2, review, and context
metadata through versioned migrations. Rebuild deterministic state from sources, manifests,
profile rules, and governed definitions; preserve accepted semantic evidence, reviewed outputs, and
frozen packs separately long enough to reattach or audit them. Compare identity, hash, and count
reports before accepting recovery.

Current recovery automatically reattaches hash-verified reviewed/pinned L2 Markdown, persisted
dynamic context definitions, and frozen context packs during a full deterministic relationship
refresh. It reconstructs their artifact and dependency records without rewriting persisted bytes.
Semantic proposal/review decisions are not derivable from source files. Retain the SQLite database
in normal backups if those decisions must survive total database loss. A relationship-ledger export
is useful audit evidence, but there is no automatic ledger-import restore command. Do not treat an
export alone as a tested substitute for the database backup. The local drill confirmed both sides
of this boundary: deterministic rebuild omitted the synthetic semantic decision, and restoring
the saved database recovered it exactly.

Repository analysis is disposable derived state under
`.mirrorarc/cache/code-intelligence/`. If its index, analysis pointers, or snapshots are suspect,
remove that directory only, then rebuild from the governed repository identity:

```bash
mirrorarc --root <vault> code doctor
mirrorarc --root <vault> code analyze --repo <repo-id>
mirrorarc --root <vault> code status --repo <repo-id>
```

Deleting this cache does not remove the repository, its L1 mirror, or manifests. Frozen code
context files under `.mirrorarc/cache/context/` are also derived; preserve one separately only when
its exact offline evidence envelope is needed for audit. A failed refresh retains the prior valid
analysis and reports `failed` until a successful rebuild.

## Rebuild PDF indexes without losing answer history

PageIndex stores current index pointers, hash-addressed index JSON, and historical answer candidates
under `.mirrorarc/cache/pageindex/<source-id>/`. Before maintenance, back up that source's whole
directory together with its frozen packs under `.mirrorarc/cache/context/`. Answers are not
recreated by model-free indexing; asking the same question again is a new inference, not a restore.

For index-only loss, preserve the `answers/` subdirectory. Move only the selected source's index
JSON files and `current.json` to a recovery folder outside the vault, then run:

```bash
mirrorarc --root /absolute/path/to/restored-vault document doctor
mirrorarc --root /absolute/path/to/restored-vault document status --source SOURCE_ID --json
mirrorarc --root /absolute/path/to/restored-vault document index --source SOURCE_ID --json
mirrorarc --root /absolute/path/to/restored-vault catalog --html --include-content
```

Use the source ID from the restored manifest. Do not add `--model-assisted` or `--allow-model`
merely to perform a restore. A source/parser change can legitimately produce a new index identity;
historical answers must remain historical. The local drill rebuilt unchanged source evidence with
the same index and frozen-pack identities, preserved all answer/frozen bytes, and made no model call.

Applied journal events now record hash-aware invalidation through that dependency graph. A failed
or skipped event does not advance invalidation state. `mirrorarc reconcile` also compares current
manifest hashes with ledger artifact hashes and repairs a missed transition; repair uses the same
bounded, cycle-safe affected-subgraph traversal as live replay.

## Recover From Interrupted Sync

Mirror writes are atomic, so an interrupted sync should preserve either the prior complete mirror or
the new complete mirror. A hard interruption can also leave a hidden atomic temp file such as
`.registration.md.12345.tmp` beside the target. After interruption:

```bash
python3.11 tools/mirrorarc.py status
python3.11 tools/mirrorarc.py recovery
python3.11 tools/mirrorarc.py sync
python3.11 tools/mirrorarc.py lint
```

If `_meta/source-manifest.json`, `_meta/repo-manifest.json`, or `_meta/sync-audit.jsonl` is missing,
restore it from backup when possible. If no backup exists, rerun status/sync to rebuild manifests
from the current sources and mirrors, then review all `planned`, `stale`, `source_missing`,
`unreachable`, and `manual_modification` states.

Interrupted Stage 1B changed-file materialization should first be inspected with
`mirrorarc journal status` and recovered with `mirrorarc journal replay`. Replay recovers
events left in `processing`; use `mirrorarc journal replay --retry-failed` only when a failed
event is ready for an explicit retry. Use `mirrorarc reconcile` to queue missed source/manifest
events before replaying recovered work, or use `mirrorarc sync --changed` to run those two steps
as one changed-file pass. `mirrorarc watch --once` runs the same startup reconciliation posture
plus any queued feed work for a deterministic one-cycle watch check. When changed sync, replay,
reconciliation, or watch startup cannot prove consistency, run full sync as the recovery path.

When an error state exists, inspect the newest `_meta/sync-audit.jsonl` event for that `source_id` or
`repo_id`. The event records the generated artifact path, lifecycle state, sync status, and
structured `warnings` / `errors` without embedding source document text or repo document bodies.
When the vault has `_meta/lifecycle-states.yml`, source/repo manifest records and audit events also
identify that lifecycle contract path and schema version so reviewers can tie a state back to the
operator contract used by sync.

Important limitation: without the old manifest, MirrorArc cannot prove whether an existing
generated region is pristine. Existing Office and repo mirrors without a manifest-generated baseline
are treated as review-required, and `--force` will not accept them as clean. If the sentinel boundary
is valid, run `mirrorarc migrate annotations --write` to preserve any legacy above-sentinel
annotations before regenerating from the original source. If the sentinel is missing or altered,
restore the mirror from backup or remove the untrusted mirror after preserving any deliberate human
authority in a declared source record, then regenerate from the source.

## Recovery Report

Use the read-only recovery report before changing files:

```bash
python3.11 tools/mirrorarc.py recovery
python3.11 tools/mirrorarc.py recovery --worksheet
python3.11 tools/mirrorarc.py recovery --runbook
python3.11 tools/mirrorarc.py recovery --json
```

The report reads `_meta/source-manifest.json`, `_meta/repo-manifest.json`,
`_meta/lifecycle-states.yml`, `tools/repos.yml`, and the latest matching events in
`_meta/sync-audit.jsonl`, then lists only records that need operator action. It does not move,
delete, regenerate, or archive anything. Use `--worksheet` when you need a Markdown review
checklist for a private pilot record before changing files. Use `--runbook` when you need a
state-grouped execution protocol for resolving the queue in a controlled batch. Treat recovery
output as triage evidence for:

- `planned`, `source_changed`, `source_moved`, `stale`, `converter_changed`, `unsupported`,
  `source_missing`, `manual_modification`, `conflict`, and `error` Office records;
- missing generated mirror paths;
- `planned`, `repo_changed`, `stale`, `unreachable`, `repo_unconfigured`,
  `manual_modification`, `conflict`, and `error` repo records;
- previously synced repo manifest records whose `tools/repos.yml` entry is now missing, even before
  the repo sync has persisted `repo_unconfigured` back to `_meta/repo-manifest.json`;
- missing repo mirror notes;
- stale atomic temp files left by interrupted writes.

The JSON form includes `summary.total`, `summary.office`, `summary.repo`, and `summary.temp`
counts for automation, plus the same item-level reasons, fallback actions, warnings, errors, and
latest audit context as the human report. Office and repo items also include a structured
`lifecycle` object from `_meta/lifecycle-states.yml` with `entry_condition`, `explanation`,
`permitted_next_actions`, `exit_condition`, and `manifest_state`. The worksheet prints the
contract-backed explanation, next actions, and exit condition for each item so operators can see
how to leave the state safely.
The runbook form groups the same queue into resolution paths for missing Office sources, moved
sources, repo mirrors whose config entry was removed, manual generated-region edits, conflicts or
errors, and stale atomic temp files. It prints execution rules and verification gates, but does not
change files.
For Office move and mirror-root conflict records, the report also includes `previous_target`,
`previous_target_exists`, and `previous_target_reason` so operators can identify the retained
generated mirror that must be preserved, moved, archived, or removed before syncing again.
For ambiguous move conflicts, the report and Office manifest record include
`ambiguous_move_candidates` with the missing source paths whose bytes match the new source. Choose
the correct history manually, or preserve/archive the old mirrors and treat the new file as a
deliberate duplicate or new source before rerunning sync. The human report shows a bounded
candidate summary with a total count; use `mirrorarc recovery --json` when the full candidate list
is longer than the human summary.
For manifest repair mistakes where multiple non-synthetic records claim the same current source
path, the report includes `duplicate_source_ids`. Correct the duplicate manifest records before
syncing; MirrorArc will not choose one source history silently.

For each item with audit history, the report includes the latest audit timestamp, status, lifecycle
state, lifecycle contract provenance when available, and structured warnings/errors. This is
diagnostic metadata only; it should not contain raw document text or repo documentation bodies.

For `temp:interrupted_write` items, rerun status/sync first to confirm the canonical generated file
or manifest is complete. Then remove the temp file after backup review; MirrorArc does not delete
it automatically.

For Office `conflict` records caused by a mirror-root or mirror-mode change, archive or remove the
previous generated mirror after review. MirrorArc will not write the new mirror path while the
old generated mirror still exists, because that would leave two generated notes claiming the same
source.

For Office `source_moved` records with `previous_mirror_path`, migrate any legacy annotations from
the old mirror, then move, archive, or remove that previous generated mirror. MirrorArc will not
write the new mirror path while the old generated mirror still exists.

For Office `conflict` records with `ambiguous_move_candidates`, do not force sync. Multiple missing
manifest records have identical bytes, so MirrorArc cannot prove which prior source path moved.
Use the candidate paths, old mirrors, and Git history/backups to choose the correct source record;
if you want to preserve one candidate's source history, edit or restore the manifest deliberately.
If the new file should be treated as a deliberate new or duplicate source, either restore the
candidate source files to their manifest paths so they are no longer missing, or deliberately edit
or remove the old candidate manifest records after preserving their old mirrors. Simply moving the
old files to an archive path without manifest resolution leaves the original manifest paths missing
and the conflict active. Rerun status after the resolution; the conflict clears once fewer than two
matching missing candidates remain.

For Office `conflict` records with `duplicate_source_ids`, do not sync until the manifest has a
single non-synthetic source record for that current source path. Keep the source ID whose history is
correct, restore the other source files to their actual paths or archive their mirrors deliberately,
then rerun status.

If a manifest is missing, restore it from backup when possible. Without manifest evidence,
MirrorArc cannot safely prove whether an existing generated region is pristine.

## Recover From Bad Generated Output

If extraction quality is poor or a converter update produces worse markdown:

1. Restore the prior mirror from Git or backup if humans need the previous readable output.
2. Keep the original source file unchanged.
3. Pin or revert the converter dependency if needed.
4. Run `tools/mirrorarc.py status` and inspect converter-related stale states.
5. Record the decision in `log.md`.

If conversion fails before writing, MirrorArc records an `error` lifecycle state and leaves the
previous mirror untouched. Fix the converter/source issue, rerun `tools/mirrorarc.py sync`, then
confirm `tools/mirrorarc.py status` returns the source to `clean`.

If writing the mirror fails, MirrorArc records an `error` lifecycle state and leaves the previous
mirror untouched. Fix the filesystem, permission, disk-space, or cloud-sync issue, rerun
`tools/mirrorarc.py sync`, then confirm the source returns to `clean`.

Repo mirror note writes follow the same rule: a write failure records an `error` lifecycle state,
keeps the previous repo note, and can recover to `clean` after the filesystem issue is fixed and
sync is rerun.

## Recover Authoritative Markdown and Reviewed Views

Authoritative Markdown is human-maintained source evidence. Reviewed L2 output is a governed
derived version. Restore both from Git or filesystem backup, not from a generated candidate. If an
agent made a bad edit:

```bash
git diff
git restore -- path/to/note.md
python3.11 tools/mirrorarc.py lint
```

Only restore with explicit owner approval when the note contains current business decisions.

## Source Missing Review

MirrorArc does not delete mirrors automatically when a source disappears. A missing source means:

- the source was intentionally moved or deleted;
- a cloud-sync file is not pinned locally;
- a path changed;
- a backup or restore is incomplete.

Resolve the source first. If the deletion is intentional, archive or remove the mirror through a
human-reviewed change and keep the audit trail.

## Release Gate

Before public release, recovery must be tested on a copied vault:

- run `tools/mirrorarc.py sandbox --source-root <original-source-root>` and resolve errors;
- move generated `_mirrors/` aside into a recovery folder and regenerate;
- interrupt sync and rerun;
- force a converter failure and verify the previous mirror is preserved, then fix the converter and
  verify sync returns the record to `clean`;
- force a mirror-write failure and verify the previous mirror is preserved, then fix the filesystem
  issue and verify sync returns the record to `clean`;
- force a repo-note write failure and verify the previous repo note is preserved, then fix the
  filesystem issue and verify sync returns the record to `clean`;
- remove one source and verify `source_missing`;
- change one source and verify `source_changed`, change mirror configuration and verify `stale`,
  and change converter metadata or version and verify `converter_changed`;
- configure one new source/repo and verify `planned`;
- change one repo fixture or HEAD and verify `repo_changed`, make a configured repo unreachable
  and verify `unreachable`, then remove a synced repo config entry and verify
  `repo_unconfigured`;
- edit a generated region and verify `manual_modification`;
- move one source and verify `source_moved` blocks new mirror generation while the previous mirror
  exists, then remove or move the previous mirror and verify the new mirror can be generated;
- change the Office mirror root with the old mirror present and verify `conflict`, then remove the
  old mirror and verify the new mirror can be generated;
- run `tools/mirrorarc.py recovery` and verify the checklist matches the manifest states;
- restore an authoritative Markdown record and a reviewed-view version from Git;
- preserve `.mirrorarc/state.sqlite` outside the copied vault, rebuild deterministic relationships/views, and compare current
  hashes and counts before accepting recovery; verify reviewed/pinned views, dynamic definitions,
  and frozen packs reattach with unchanged bytes;
- run no-data scan and lint after recovery.

Stage 1B adds recovery gates for journal replay, missed-event reconciliation, stale-lock recovery,
duplicate event delivery, crash after mirror write but before checkpoint, and full-sync recovery
after journal loss. The current replay path covers interrupted `processing` events and explicit
failed-event retry; the current explicit reconciliation path queues missed create, update, delete,
move, and review-required candidate events; the current `watch --once` path runs deterministic
startup reconciliation, feed queueing, and replay; manifest-backed deleted events now mark records
`source_missing` while retaining generated mirrors; resolved `source_moved` records replay after
old-mirror cleanup, and delete/recreate can return records to `clean`. Optional `watch --native`
capture now maps watchdog events through the same feed/replay boundary. The Stage 1B safety-gate
closure records focused, affected, full-suite, packaging, lint, no-data, template-copy, shell
syntax, diff, and residue validation.

The test suite now exercises the copied-vault regeneration path, source-byte preservation,
converter-failure, Office mirror-write-failure, and repo-note write-failure recovery that preserve
the prior generated file, interrupted-write temp detection, conversion-race aborts that preserve
the prior mirror, `source_missing`, `manual_modification`, lint, and generated-text no-data scan
checks on the Northwind example. Example regeneration tests also assert source bytes stay unchanged
across plan, dry-run, sync, status, and lint operations, and that stable generated outputs remain
unchanged across a second sync.
The installed-wheel synthetic drill also passed copied-vault sandbox checks with zero errors,
generated-mirror loss/rebuild, lint, and a no-data scan of the generated HTML, mirror and reviewed
view. Sandbox warnings about a missing unused repo manifest and the parent Git workspace were
retained; no files were staged or committed. Operator backup/restore drills and full copied-vault
no-data scans on actual pilot vaults remain required before production use.

A snapshot-identity mismatch indicates a source mutation during copying or modified disposable
cache. The operation fails without replacing the prior valid analysis. Confirm the source is
stable, remove only the disposable code-intelligence cache, and retry once; do not remove sources
or frozen audit evidence. `--base REF` compares the base commit to the analyzed working tree,
including staged, unstaged and untracked paths, with both sides of renames and deleted-path
omissions. It is not a committed merge-base-to-HEAD comparison.

Full `mirrorarc sync` reconciles manifest hash changes through the existing dependency invalidator,
including marking frozen contexts stale while preserving their bytes. Query refresh performs the
same reconciliation before graph replacement, so a refresh cannot erase the previous hash first.
