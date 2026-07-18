# NoeticWeave

**Compile changing source collections into governed, profile-driven knowledge workspaces without
modifying the original records.**

NoeticWeave is a pre-release methodology + small toolkit for source-backed knowledge workspaces.
The first commercial wedge remains consulting and implementation teams with document-heavy client
work, but the core is now converging toward profile-driven workspaces for business operations,
research/learning, software-project documentation, and minimal blank starts. You bring source files,
a local vault, an AI coding agent (Claude Code, OpenAI Codex, etc.), and optionally
[Obsidian](https://obsidian.md) as a reference human UI.

NoeticWeave is the new project identity for the technical alpha formerly called Vaultwright.
“Noetic” points to knowledge and understanding; “weave” describes the product's job of connecting
changing sources, governed mirrors, provenance, and curated knowledge into one inspectable
workspace. The initially proposed **NoeticLens** was rejected after an exact-name collision check.
See [ADR 0003](docs/adr/0003-noeticweave-project-identity.md) for the naming decision and technical
migration boundary.

> Inspired by Andrej Karpathy's ["LLM wiki" pattern](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
> Honest about the landscape — see [`docs/positioning.md`](docs/positioning.md).

## The problem

- **Silos.** Your contracts, decks, spreadsheets, repos, and notes don't know about each other.
- **"When everything is documented, nothing is."** Naive AI doc-generation *spawns* files until
  the pile is unusable.
- **RAG re-derives every time.** Chat-over-your-files tools answer from a vector index and forget;
  nothing is *built up*.

## What makes NoeticWeave different

Most "AI second brain in Obsidian" projects stop at the wiki pattern. NoeticWeave leads with the
parts nobody else ships:

1. **The mirror layer.** Your Office files (`.docx/.pptx/.xlsx`, via Microsoft
   [markitdown](https://github.com/microsoft/markitdown)) and your **GitHub repos** get
   auto-generated markdown **mirrors** that refresh when the original changes (content-hashed,
   idempotent). Office mirrors live under `_mirrors/` so raw source folders stay clean; text-based
   PDF mirrors are available with `sync_office_md.py --include-pdf` or by setting
   `office_mirrors.include_pdf: true` in `_meta/mirror-config.yml` for unattended syncs. The
   original stays the source of truth; the mirror is searchable, linkable, diffable, and easier for
   agents to inspect than opaque binaries. Generated mirrors are machine-owned; durable human notes
   belong in curated notes or migrated `_meta/mirror-annotations/` sidecars.
2. **Linking-first retrieval.** Maps of Content, entity pages, backlinks, and a frontmatter-driven
   index (Obsidian **Bases**) are the initial retrieval engine. `noeticweave catalog` also
   generates a path-and-metadata-only `CATALOG.md` gateway for reviewers and agents that do not use
   Obsidian. Vector or semantic indexes may help later, but they are not the source of truth.
3. **Anti-proliferation discipline.** The agent is told to **consolidate and update before
   creating**, and the linter flags structural drift plus likely note overlap with review-only
   consolidation suggestions. Restraint is a feature.
4. **Governance for real business records.** PII isolation, a retention policy, and
   secrets-stay-out-of-the-vault — because this holds finance, governance, customer, people, and
   operational records, not just personal notes.

## Who it's for

Small consulting, advisory, implementation, and operations teams that receive messy client or
engagement document collections and need to turn them into governed, source-linked operating
knowledge. Owner-operators may benefit later, but the first release is scoped around teams that
already understand provenance, engagement boundaries, and source preservation.

## How it works (seven layers)

| Layer | What | Who owns it |
| --- | --- | --- |
| **Sources** | original files, repositories, exports, and external records | authoritative; never altered by NoeticWeave |
| **Change journal** | future ordered local observations, retries, and materialization checkpoints | operational, derived state |
| **Mirrors** | machine-generated Markdown and extraction metadata | derived, reproducible artifacts |
| **Curated knowledge** | human-reviewed notes, syntheses, entities, and decisions | human-governed |
| **Profile** | domain vocabulary, schemas, templates, views, skills, and benchmarks | versioned contract |
| **Evidence index** | future full-text/graph cache for retrieval and context assembly | disposable derived cache |
| **Presentation** | Obsidian, catalogs, Canvas, Explorer, MCP, and context packs | derived interfaces |

Product contract: [`docs/PRODUCT.md`](docs/PRODUCT.md). Sync contract:
[`docs/SYNC_SPEC.md`](docs/SYNC_SPEC.md). Security model:
[`docs/SECURITY_MODEL.md`](docs/SECURITY_MODEL.md). Recovery guide:
[`docs/RECOVERY.md`](docs/RECOVERY.md). Design-partner protocol:
[`docs/DESIGN_PARTNER_PROTOCOL.md`](docs/DESIGN_PARTNER_PROTOCOL.md).
Design-partner recruiting:
[`docs/DESIGN_PARTNER_RECRUITING.md`](docs/DESIGN_PARTNER_RECRUITING.md).
First external pilot runbook:
[`docs/FIRST_EXTERNAL_PILOT_RUNBOOK.md`](docs/FIRST_EXTERNAL_PILOT_RUNBOOK.md).
Stage 3 validation status:
[`docs/STAGE3_VALIDATION_STATUS.md`](docs/STAGE3_VALIDATION_STATUS.md).
Validation gate:
[`docs/VALIDATION_GATE.md`](docs/VALIDATION_GATE.md).
Conversion review guide:
[`docs/CONVERSION_REVIEW_GUIDE.md`](docs/CONVERSION_REVIEW_GUIDE.md).
Release checklist:
[`docs/RELEASE.md`](docs/RELEASE.md).
Agent-readiness benchmark:
[`docs/AGENT_READINESS_BENCHMARK.md`](docs/AGENT_READINESS_BENCHMARK.md).
Public benchmark results:
[`docs/AGENT_READINESS_BENCHMARK_RESULTS.md`](docs/AGENT_READINESS_BENCHMARK_RESULTS.md).
Full write-up: [`docs/methodology.md`](docs/methodology.md).
Professional review brief: [`docs/NOETICWEAVE_WHITEPAPER.md`](docs/NOETICWEAVE_WHITEPAPER.md).
Current v1 architecture decision:
[`docs/adr/0001-profile-driven-v1-architecture.md`](docs/adr/0001-profile-driven-v1-architecture.md).
Journaled incremental materialization decision:
[`docs/adr/0002-journaled-incremental-materialization.md`](docs/adr/0002-journaled-incremental-materialization.md).
Project identity decision:
[`docs/adr/0003-noeticweave-project-identity.md`](docs/adr/0003-noeticweave-project-identity.md).
Finish-line matrix: [`docs/V1_FINISH_LINE.md`](docs/V1_FINISH_LINE.md).

## Quick start

Create a vault without cloning NoeticWeave itself. The installable command requires Python 3.11+;
`uvx` and `pipx run` will build an isolated environment when they can find a compatible Python.
Before the package is published to PyPI, use the Git URL:

```bash
uvx --from git+https://github.com/cz1993/noeticweave.git noeticweave init --profile business-operations ~/my-business-vault

# or, with pipx:
pipx run --spec git+https://github.com/cz1993/noeticweave.git noeticweave init --profile business-operations ~/my-business-vault
```

Once NoeticWeave is published to PyPI, the equivalent short forms are
`uvx noeticweave init --profile business-operations ~/my-business-vault` and
`pipx run noeticweave init --profile business-operations ~/my-business-vault`.

For repeated local use, install the console command once:

```bash
uv tool install git+https://github.com/cz1993/noeticweave.git
noeticweave --version

# or, with pipx:
pipx install git+https://github.com/cz1993/noeticweave.git
noeticweave --version
```

Then open the vault in Obsidian if you want a human UI, point your agent at it (it reads
`CLAUDE.md` first), and run the installed command from any folder:

```bash
noeticweave --root ~/my-business-vault doctor          # check dependencies and vault structure
noeticweave --root ~/my-business-vault plan            # inspect proposed mirror actions first
noeticweave --root ~/my-business-vault sync            # mirror Office files and configured repos
noeticweave --root ~/my-business-vault status          # review manifest-backed lifecycle state
noeticweave --root ~/my-business-vault sync --json     # machine-readable sync evidence for agents/pilots
noeticweave --root ~/my-business-vault status --json   # machine-readable lifecycle status
noeticweave --root ~/my-business-vault doctor --json   # machine-readable preflight report
noeticweave --root ~/my-business-vault conversion --guide   # read-only conversion spot-check + guide
noeticweave --root ~/my-business-vault conversion --init-results # private quality review scaffold
noeticweave --root ~/my-business-vault conversion --results _meta/conversion-quality-results.yml --require-reviewed # after filling scaffold
noeticweave --root ~/my-business-vault migration       # dry-run report for legacy/unknown folders
noeticweave --root ~/my-business-vault migration --runbook  # legacy folder move protocol
noeticweave --root ~/my-business-vault migration --normalize-frontmatter-domains --worksheet # review domain alias cleanup
noeticweave --root ~/my-business-vault recovery --worksheet # review manifest recovery actions
noeticweave --root ~/my-business-vault sandbox --source-root /path/to/original-documents
noeticweave --root ~/my-business-vault catalog         # generate CATALOG.md inventory gateway
noeticweave --root ~/my-business-vault catalog --html  # generate CATALOG.html visual inventory gateway
noeticweave --root ~/my-business-vault m365            # Microsoft 365/Copilot handoff readiness
noeticweave --root ~/my-business-vault review --json   # summarize metadata-only human review decisions
noeticweave --root ~/my-business-vault overlap         # calibrate overlap thresholds without note bodies
noeticweave --root ~/my-business-vault pilot           # aggregate pilot evidence, no source content
noeticweave --root ~/my-business-vault pilot --worksheet    # redacted Markdown private-pilot summary
noeticweave --root ~/my-business-vault benchmark            # validate agent-readiness task pack, if present
noeticweave --root ~/my-business-vault benchmark --init-tasks    # create private task scaffold
noeticweave --root ~/my-business-vault benchmark --worksheet     # print private benchmark run sheet
noeticweave --root ~/my-business-vault benchmark --init-results  # create private result scaffold
noeticweave --root ~/my-business-vault benchmark --results _meta/agent-readiness-results.yml --require-prompt-safety # after scoring
# edit tools/repos.yml, then:
noeticweave --root ~/my-business-vault sync           # mirror configured GitHub repos too
noeticweave --root ~/my-business-vault lint           # health check
```

Run `sandbox` from a duplicated pilot vault, not the original document folder. It is read-only and
checks copy-boundary, mirror isolation, manifest/recovery readiness, and basic backup posture
without printing source paths or document text.

Use `review` after spot-checking mirrors, catalogs, or handoff reports. It appends metadata-only
decisions to `_meta/review-ledger.jsonl` with artifact hashes, so later changes are reported as
stale reviews instead of silently preserving old approvals.

Source checkout fallback:

```bash
git clone https://github.com/cz1993/noeticweave.git noeticweave && cd noeticweave
python3.11 -m pip install -e .
noeticweave --version
noeticweave profile list
noeticweave init --profile business-operations ~/my-business-vault
noeticweave init --profile research-learning ~/my-research-vault
noeticweave init --profile software-project ~/my-software-vault
noeticweave init --profile blank ~/my-blank-vault
noeticweave --root ~/my-business-vault profile validate
noeticweave --root ~/my-business-vault profile diff 0.1.0
noeticweave --root ~/my-business-vault profile migrate --plan
noeticweave --root ~/my-business-vault profile migrate --write
noeticweave --root ~/my-business-vault profile views --check
noeticweave --root ~/my-business-vault migrate annotations --plan
noeticweave --root ~/my-business-vault plan
```

The packaged v1 profiles are `business-operations`, `research-learning`, `software-project`, and
`blank`. Each initializes from the installable package; non-business profiles get profile-owned
starter folders, `_meta/profile.yml`, generated scaffold docs, and only the templates declared by
their contracts.

Profile contract details: [`docs/PROFILE_SCHEMA.md`](docs/PROFILE_SCHEMA.md).

Step-by-step: [`docs/quickstart.md`](docs/quickstart.md).

## Status

**v0 - technical alpha.** The template vault, schema, thin tool CLI, source-installable console
entry point, sync/lint tools, examples, safety guards, Office/repo manifests, audit logs,
journaled changed-file materialization, and all four official profile init fixtures work today.
The v1 finish line now pulls external corpus validation ahead of optional Obsidian adapter,
indexing, Explorer, and visualization work, with explicit stop/pivot rules in the validation gate.
Full sync remains the baseline and recovery path; journaled incremental operation is the
steady-state changed-file path.

## License

NoeticWeave is licensed under the GNU Affero General Public License v3.0 or later for the open
core, with a separate **commercial license** planned for enterprise/closed use and consulting.
`LICENSE` contains the full AGPL-3.0 text; commercial terms and contribution policy still require
owner/counsel finalization before accepting outside contributions. See [`LICENSING.md`](LICENSING.md).
"NoeticWeave" is a trademark — see [`TRADEMARK.md`](TRADEMARK.md).

## Credits

The "LLM wiki" pattern (Andrej Karpathy), [markitdown](https://github.com/microsoft/markitdown)
(Microsoft), and [Obsidian](https://obsidian.md). Interoperates with — rather than competes with —
tools like [basic-memory](https://github.com/basicmachines-co/basic-memory) and Copilot for
Obsidian.
