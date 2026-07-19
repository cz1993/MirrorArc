# Quickstart

Aimed at a technical founder/owner who knows git. ~15 minutes.

## Prerequisites

- [Obsidian](https://obsidian.md) (free) — optional reference human UI.
- Python 3.11+ and `git`.
- An AI coding agent that reads a `CLAUDE.md` / `AGENTS.md`: Claude Code, OpenAI Codex, etc.
- Optional: GitHub CLI (`gh`) if you'll mirror private repos.

## 1. Create your vault

Create the vault without cloning MirrorArc itself. The installable command requires Python 3.11+;
`uvx` and `pipx run` create isolated environments when they can find a compatible Python.

```bash
uvx --from git+https://github.com/cz1993/MirrorArc.git mirrorarc init --profile business-operations ~/my-business-vault

# or, with pipx:
pipx run --spec git+https://github.com/cz1993/MirrorArc.git mirrorarc init --profile business-operations ~/my-business-vault
```

Once MirrorArc is published to PyPI, the equivalent short forms are
`uvx mirrorarc init --profile business-operations ~/my-business-vault` and
`pipx run mirrorarc init --profile business-operations ~/my-business-vault`.

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
mirrorarc init --profile business-operations ~/my-business-vault
mirrorarc init --profile research-learning ~/my-research-vault
mirrorarc init --profile software-project ~/my-software-vault
mirrorarc init --profile blank ~/my-blank-vault
mirrorarc --root ~/my-business-vault profile validate
mirrorarc --root ~/my-business-vault profile diff 0.1.0
mirrorarc --root ~/my-business-vault profile migrate --plan
mirrorarc --root ~/my-business-vault profile migrate --write
mirrorarc --root ~/my-business-vault profile views --check
mirrorarc --root ~/my-business-vault migrate annotations --plan
```

Packaged profile contracts now include `business-operations`, `research-learning`,
`software-project`, and `blank`. Each initializes through `mirrorarc init --profile <profile-id>`;
non-business starters derive their folders, scaffold docs, domain map, and note templates from the
selected profile contract.

Profile schema reference: [`PROFILE_SCHEMA.md`](PROFILE_SCHEMA.md).

## 2. Open it in Obsidian

"Open folder as vault" → `~/my-business-vault`. Enable the core plugins **Properties**, **Bases**,
and **Graph** (Settings → Core plugins). Open `Documents.base` to see the auto-generated index.

Obsidian is useful for people, but it is not the correctness boundary. The key artifact is the
filesystem of markdown mirrors, manifests, and curated notes that your agent can inspect directly.

## 3. Point your agent at it

Open the vault with your agent (e.g. run Claude Code / Codex in the folder). It reads `CLAUDE.md`
first — that's the operating manual. Try: *"Read CLAUDE.md, then ingest the file I just added to
`60_finance/` following the schema."*

## 4. Mirror your binaries and repos

```bash
# optional: copy tools/repos.example.yml to tools/repos.yml in the vault, then edit to list repos
gh auth login                                        # read-only is enough (or export GH_TOKEN)

mirrorarc --root ~/my-business-vault doctor        # check dependencies and vault structure
mirrorarc --root ~/my-business-vault sandbox --source-root /path/to/original-documents # copied-vault preflight
mirrorarc --root ~/my-business-vault plan          # inspect source inventory and proposed mirrors
mirrorarc --root ~/my-business-vault sync          # mirrors -> _mirrors/ and profile repo_notes_dir
mirrorarc --root ~/my-business-vault sync --json   # machine-readable sync evidence
mirrorarc --root ~/my-business-vault status        # review manifest-backed lifecycle state
mirrorarc --root ~/my-business-vault status --json # machine-readable lifecycle status
mirrorarc --root ~/my-business-vault doctor --json # machine-readable preflight report
mirrorarc --root ~/my-business-vault catalog       # write CATALOG.md inventory gateway
mirrorarc --root ~/my-business-vault catalog --html # write CATALOG.html visual inventory gateway
mirrorarc --root ~/my-business-vault m365          # Microsoft 365/Copilot handoff readiness
mirrorarc --root ~/my-business-vault review --json # summarize metadata-only review decisions
mirrorarc --root ~/my-business-vault overlap       # calibrate overlap thresholds without note bodies
mirrorarc --root ~/my-business-vault conversion --guide # read-only conversion spot-check and guide
mirrorarc --root ~/my-business-vault conversion --init-results # private quality result scaffold
mirrorarc --root ~/my-business-vault conversion --results _meta/conversion-quality-results.yml --require-reviewed # after filling scaffold
mirrorarc --root ~/my-business-vault migration     # dry-run report for legacy/unknown folders
mirrorarc --root ~/my-business-vault migration --worksheet # Markdown cleanup checklist
mirrorarc --root ~/my-business-vault migration --runbook # legacy folder move protocol
mirrorarc --root ~/my-business-vault migration --normalize-frontmatter-domains --worksheet # domain cleanup checklist
mirrorarc --root ~/my-business-vault recovery --worksheet # manifest recovery checklist
mirrorarc --root ~/my-business-vault pilot         # aggregate pilot evidence, no source content
mirrorarc --root ~/my-business-vault pilot --worksheet # redacted Markdown private-pilot summary
mirrorarc --root ~/my-business-vault benchmark     # validate benchmark tasks, if configured

mirrorarc --root ~/my-business-vault lint          # health check
```

## 5. Keep it fresh (unattended)

`tools/sync_all.sh` runs both syncs + the linter. Schedule it daily on the machine that holds the
vault:

If the vault should keep text-based PDF mirrors fresh too, set `office_mirrors.include_pdf: true`
in `_meta/mirror-config.yml`; `sync_all.sh` will honor that setting.

```cron
0 7 * * * cd "$HOME/my-business-vault" && bash tools/sync_all.sh >> _tmp/sync.log 2>&1
```

## Daily use

- **New document?** Drop the original in the right folder and ask the agent to *ingest* it — it
  will mirror binaries under `_mirrors/`, create or **extend** a note, link it from the relevant
  hub/entity, and log it.
- **A question?** Ask the agent; it reads `INDEX.md` / the MOCs first and answers with citations.
- **Need a non-Obsidian gateway?** Regenerate `CATALOG.md` with
  `mirrorarc --root ~/my-business-vault catalog`, or `CATALOG.html` with
  `mirrorarc --root ~/my-business-vault catalog --html`; both list source paths, mirrors,
  lifecycle states, and inventory stats without copying content. The HTML gateway adds static
  aggregate charts for quick review.
- **Reviewed an artifact?** Record the decision with
  `mirrorarc --root ~/my-business-vault review --artifact CATALOG.html --status approved --reviewer <name>`.
  The ledger stores hashes and short metadata notes only, then reports approvals as stale if the
  reviewed artifact changes.
- **Housekeeping?** Ask it to *lint* — or just run `mirrorarc --root ~/my-business-vault lint`.
- **Remember:** prefer consolidating into existing notes over creating new ones. See
  `docs/methodology.md` §4.
- **Agent-readiness pilot?** Use `docs/AGENT_READINESS_BENCHMARK.md` and
  `mirrorarc --root ~/my-business-vault benchmark --init-tasks` to create a private task scaffold
  after sync, then `mirrorarc --root ~/my-business-vault benchmark --worksheet` to run the
  comparison, then `mirrorarc --root ~/my-business-vault benchmark --init-results` and
  `mirrorarc --root ~/my-business-vault benchmark --results _meta/agent-readiness-results.yml`
  to compare raw-source, plain markitdown dump, and MirrorArc-markdown performance on the same questions. Add
  `--require-citations` and `--require-prompt-safety` when pilot results must prove source-backed
  answers and prompt-injection handling.
- **Microsoft 365 handoff?** Use `docs/MICROSOFT_365_HANDOFF.md` and
  `mirrorarc --root ~/my-business-vault m365` to check whether the generated mirror/catalog layer
  is ready for a governed SharePoint, OneDrive, Copilot Studio, or connector review.
