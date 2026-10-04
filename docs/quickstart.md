# Quickstart

Aimed at a technical founder/owner who knows git. ~15 minutes.

## Preview the flagship example first

Open the **[hosted Ontario Grid demo](https://cz1993.github.io/MirrorArc/)** and start with the
pinned `INDEX.md` five-minute tour. It is generated from MirrorArc's provenance-documented public
example and passes the repository no-data and vault-lint gates before deployment. The hosted build
also publishes a [crawlable project overview](https://cz1993.github.io/MirrorArc/project/) that
identifies the canonical GitHub source, plus a
[crawlable documentation index](https://cz1993.github.io/MirrorArc/documents/),
[sitemap](https://cz1993.github.io/MirrorArc/sitemap.xml), and
[agent discovery file](https://cz1993.github.io/MirrorArc/llms.txt); the local catalog command does
not publish or expose a private vault.

To rebuild the same public Ontario Electricity example locally from a source checkout:

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
mirrorarc --root examples/ontario-electricity-evidence-vault sync
mirrorarc --root examples/ontario-electricity-evidence-vault catalog --html --include-content
python -m http.server 8000 --directory examples/ontario-electricity-evidence-vault
```

Open `http://127.0.0.1:8000/CATALOG.html`. The pinned `INDEX.md` is a five-minute beginner tour.
Use the resizable catalog panel to browse full filenames, then compare **Relationship map**,
**Document metadata**, and **Document view**. A content-enabled artifact from any private or
proprietary vault must remain local. The hosted demo is a narrow public-corpus exception enforced
by a dedicated build and no-data scan.

## Prerequisites

- [Obsidian](https://obsidian.md) (free) — optional reference human UI.
- Python 3.11+ and `git`.
- An AI coding agent that reads a `CLAUDE.md` / `AGENTS.md`: Claude Code, OpenAI Codex, etc.
- Optional: GitHub CLI (`gh`) if you'll mirror private repos.

## 1. Create your vault

Create the vault without cloning MirrorArc itself. The installable command requires Python 3.11+;
`uvx` and `pipx run` create isolated environments when they can find a compatible Python.

```bash
uvx --from git+https://github.com/cz1993/MirrorArc.git mirrorarc init --profile data-product ~/my-data-product

# or, with pipx:
pipx run --spec git+https://github.com/cz1993/MirrorArc.git mirrorarc init --profile data-product ~/my-data-product
```

Once MirrorArc is published to PyPI, the equivalent short forms are
`uvx mirrorarc init --profile data-product ~/my-data-product` and
`pipx run mirrorarc init --profile data-product ~/my-data-product`.

For repeated pilot commands, install the console command once:

```bash
uv tool install git+https://github.com/cz1993/MirrorArc.git
mirrorarc --version

# or, with pipx:
pipx install git+https://github.com/cz1993/MirrorArc.git
mirrorarc --version
```

Source checkout fallback:

```bash
git clone https://github.com/cz1993/MirrorArc.git mirrorarc && cd mirrorarc
python3.11 -m pip install -e .
mirrorarc --version
mirrorarc profile list
mirrorarc init --profile data-product ~/my-data-product
mirrorarc init --profile business-operations ~/my-business-vault
mirrorarc init --profile research-learning ~/my-research-vault
mirrorarc init --profile software-project ~/my-software-vault
mirrorarc init --profile blank ~/my-blank-vault
mirrorarc --root ~/my-data-product profile validate
mirrorarc --root ~/my-data-product profile diff 0.2.0
mirrorarc --root ~/my-data-product profile migrate --plan
mirrorarc --root ~/my-data-product profile migrate --write
mirrorarc --root ~/my-data-product profile views --check
mirrorarc --root ~/my-data-product migrate annotations --plan
```

Packaged profile contracts include `data-product` (the default), `business-operations`,
`research-learning`, `software-project`, and `blank`. Each initializes through
`mirrorarc init --profile <profile-id>` and derives its folders, scaffold docs, domain map, and note
templates from the selected contract.

Profile schema reference: [`PROFILE_SCHEMA.md`](PROFILE_SCHEMA.md).

## 2. Open it in Obsidian

"Open folder as vault" → `~/my-data-product`. Enable the core plugins **Properties**, **Bases**,
and **Graph** (Settings → Core plugins). Open `Documents.base` to see the auto-generated index.

Obsidian is useful for people, but it is not the correctness boundary. The key artifact is the
filesystem of authoritative records, L1 projections, manifests, evidenced relationships, governed
views, and context definitions that your agent can inspect directly.

## 3. Point your agent at it

Open the vault with your agent (e.g. run Claude Code / Codex in the folder). `CLAUDE.md` routes every
agent to `_meta/agent-rules.md`, the shared operating manual. Try: *"Read CLAUDE.md and
`_meta/agent-rules.md`, then ingest the file I added to `20_sources/` following the profile
contract."*

## 4. Mirror your binaries and repos

```bash
# optional: copy tools/repos.example.yml to tools/repos.yml in the vault, then edit to list repos
gh auth login                                        # read-only is enough (or export GH_TOKEN)

mirrorarc --root ~/my-data-product doctor        # check dependencies and vault structure
mirrorarc --root ~/my-data-product sandbox --source-root /path/to/original-documents # copied-vault preflight
mirrorarc --root ~/my-data-product plan          # inspect source inventory and proposed mirrors
mirrorarc --root ~/my-data-product inventory     # verify source/L1/L2 counts and projection ownership
mirrorarc --root ~/my-data-product sync          # mirrors -> _mirrors/ and profile repo_notes_dir
mirrorarc --root ~/my-data-product sync --json   # machine-readable sync evidence
mirrorarc --root ~/my-data-product status        # review manifest-backed lifecycle state
mirrorarc --root ~/my-data-product status --json # machine-readable lifecycle status
mirrorarc --root ~/my-data-product doctor --json # machine-readable preflight report
mirrorarc --root ~/my-data-product catalog       # write CATALOG.md inventory gateway
mirrorarc --root ~/my-data-product catalog --html # write the interactive CATALOG.html explorer
mirrorarc --root ~/my-data-product catalog --html --include-content # local rendered-content review
mirrorarc --root ~/my-data-product m365          # Microsoft 365/Copilot handoff readiness
mirrorarc --root ~/my-data-product review --json # summarize metadata-only review decisions
mirrorarc --root ~/my-data-product overlap       # calibrate overlap thresholds without note bodies
mirrorarc --root ~/my-data-product conversion --guide # read-only conversion spot-check and guide
mirrorarc --root ~/my-data-product conversion --init-results # private quality result scaffold
mirrorarc --root ~/my-data-product conversion --results _meta/conversion-quality-results.yml --require-reviewed # after filling scaffold
mirrorarc --root ~/my-data-product migration     # dry-run report for legacy/unknown folders
mirrorarc --root ~/my-data-product migration --worksheet # Markdown cleanup checklist
mirrorarc --root ~/my-data-product migration --runbook # legacy folder move protocol
mirrorarc --root ~/my-data-product migration --json # includes complete Markdown category inventory
mirrorarc --root ~/my-data-product migration --apply-markdown-review review.json --backup-dir /safe/backup --write
mirrorarc --root ~/my-data-product migration --normalize-frontmatter-domains --worksheet # domain cleanup checklist
mirrorarc --root ~/my-data-product recovery --worksheet # manifest recovery checklist
mirrorarc --root ~/my-data-product pilot         # aggregate pilot evidence, no source content
mirrorarc --root ~/my-data-product pilot --worksheet # redacted Markdown private-pilot summary
mirrorarc --root ~/my-data-product benchmark     # validate benchmark tasks, if configured
mirrorarc --root ~/my-data-product relationships refresh # deterministic relationship ledger
mirrorarc --root ~/my-data-product relationships status  # evidence/review/invalidation counts
mirrorarc --root ~/my-data-product relationships export --current # metadata-only current graph
mirrorarc --root ~/my-data-product relationships propose --help   # evidence-backed semantic proposal
mirrorarc --root ~/my-data-product relationships review --help    # named accept/reject decision
mirrorarc --root ~/my-data-product view list             # configured L2 lenses and states
mirrorarc --root ~/my-data-product view render orientation # ephemeral many-to-few view
mirrorarc --root ~/my-data-product view status             # generated/reviewed/stale counts
mirrorarc --root ~/my-data-product view review <view-id> --reviewer <name> # preserve reviewed output
mirrorarc --root ~/my-data-product context build --lens orientation --mode metadata # body-free selection manifest
mirrorarc --root ~/my-data-product context build --lens orientation --mode dynamic  # saved live definition
mirrorarc --root ~/my-data-product context resolve <definition-id>                  # current selection
mirrorarc --root ~/my-data-product context freeze --definition <definition-id>      # immutable offline pack
mirrorarc --root ~/my-data-product context status <context-id>                      # newer-version warning

# Optional repository intelligence (after configuring and syncing tools/repos.yml)
mirrorarc --root ~/my-data-product code doctor
mirrorarc --root ~/my-data-product code analyze --repo <repo-id>
mirrorarc --root ~/my-data-product catalog --html

mirrorarc --root ~/my-data-product lint          # health check
```

### Optional repository intelligence

`code doctor` either prints `Ready`, one pinned setup command, or one exact problem. MirrorArc does
not install the helper for you. The supported standalone helper is CodeGraph v1.5.0:

```bash
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/v1.5.0/install.sh \
  | CODEGRAPH_VERSION=v1.5.0 sh
mirrorarc --root ~/my-data-product code doctor
mirrorarc --root ~/my-data-product code analyze --repo <repo-id> --symbol <symbol> --context frozen
mirrorarc --root ~/my-data-product code status --repo <repo-id>
```

| Result | Meaning | Next step |
| --- | --- | --- |
| `Setup needed` | The optional helper is missing. | Run the displayed pinned install command, then retry `code doctor`. |
| `Attention` | Version, repository identity, path, or sync is not ready. | Follow the exact command printed by the doctor. |
| `stale` | The repository commit or local tree changed. | Re-run `code analyze`; the old result remains historical. |
| `failed` | Refresh failed and the last valid result was retained. | Fix the reported local issue, then re-run `code analyze`. |

Use `--changed-path <path>` for a controlled local change or `--base <ref>` for a configured local
Git repository. Affected tests are candidates, never a substitute for the repository's normal test
gate. Default Catalog HTML contains hashes, paths, and lines but no code bodies; protect
`--include-content` output like the vault.

## 5. Keep it fresh (unattended)

`tools/sync_all.sh` runs both syncs + the linter. Schedule it daily on the machine that holds the
vault:

If the vault should keep text-based PDF mirrors fresh too, set `office_mirrors.include_pdf: true`
in `_meta/mirror-config.yml`; `sync_all.sh` will honor that setting.

```cron
0 7 * * * cd "$HOME/my-business-vault" && bash tools/sync_all.sh >> _tmp/sync.log 2>&1
```

## Daily use

- **New document?** Add the original to a declared source/domain root, review `plan`, then sync its
  L1 projection and refresh deterministic relationships. Persist interpretation only when a
  configured L2 pin/review or explicit authoritative promotion requires it.
- **A question?** Ask the agent to resolve a configured view or dynamic/frozen context definition
  and answer with source-backed citations.
- **Need a non-Obsidian gateway?** Regenerate `CATALOG.md` with
  `mirrorarc --root ~/my-data-product catalog`, or `CATALOG.html` with
  `mirrorarc --root ~/my-data-product catalog --html`; both default to paths, mirrors, lifecycle
  states, and inventory metadata without copying document bodies. The HTML gateway opens on
  `INDEX.md`, separates its relationship, metadata, document, and repository Code views, and keeps Markdown/JSON
  context-pack downloads metadata-only. For local body review, add `--include-content`; protect the
  resulting HTML like the vault because it embeds bounded Markdown and generated-mirror content.
- **Reviewed an artifact?** Record the decision with
  `mirrorarc --root ~/my-data-product review --artifact CATALOG.html --status approved --reviewer <name>`.
  The ledger stores hashes and short metadata notes only, then reports approvals as stale if the
  reviewed artifact changes.
- **Housekeeping?** Ask it to *lint* — or just run `mirrorarc --root ~/my-data-product lint`.
- **Remember:** relationships are data and synthesis is a view. Durable Markdown requires an
  allowed category and explicit persistence reason.
- **Agent-readiness pilot?** Use `docs/AGENT_READINESS_BENCHMARK.md` and
  `mirrorarc --root ~/my-data-product benchmark --init-tasks` to create a private task scaffold
  after sync, then `mirrorarc --root ~/my-data-product benchmark --worksheet` to run the
  comparison, then `mirrorarc --root ~/my-data-product benchmark --init-results` and
  `mirrorarc --root ~/my-data-product benchmark --results _meta/agent-readiness-results.yml`
  to compare raw-source, plain markitdown dump, and MirrorArc-markdown performance on the same questions. Add
  `--require-citations` and `--require-prompt-safety` when pilot results must prove source-backed
  answers and prompt-injection handling.
- **Microsoft 365 handoff?** Use `docs/MICROSOFT_365_HANDOFF.md` and
  `mirrorarc --root ~/my-data-product m365` to check whether the generated mirror/catalog layer
  is ready for a governed SharePoint, OneDrive, Copilot Studio, or connector review.

## Task to evidence to export

After sync, run `mirrorarc context build --lens orientation --mode metadata --query "inspection interval" --json`.
Inspect selected spans, source hashes, ranking reasons and exclusions. Save the same query with
`--mode dynamic`, resolve its definition ID, then use `mirrorarc context freeze --definition <id>`.
The final JSON has an exact UTF-8 byte ceiling and a labeled token estimate; a reference-only
selection does not contain execution evidence. Query ranking is opt-in and can miss useful sources.

Generate `mirrorarc catalog --html` and open the portable file. The selection dialog distinguishes
metadata downloads from saved task commands and frozen context status. `--include-content` embeds
bodies explicitly and inherits source sensitivity. After changes, sync, resolve, inspect warnings
and rebuild the Catalog. Keep old frozen evidence for reproducibility; do not silently replace it.
