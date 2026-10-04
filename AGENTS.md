# AGENTS.md — rules for any agent working on the MirrorArc **codebase**

> This governs development of MirrorArc itself (Codex, Claude, etc.). It is **not** the schema
> for a user's vault — that lives in `template/_meta/profile.yml`, with runtime guidance in
> `template/_meta/agent-rules.md`. Read `README.md`, `docs/PRODUCT.md`,
> and the relevant public specification under `docs/` before changing behavior.

## What this repo is

MirrorArc is the **tool + framework + methodology** for an AI-maintained, linked-markdown
knowledge base. **This repo never contains a real knowledge base.** It contains code, docs,
templates, tests, and *sample* data only.

## Ownership (non-negotiable)

- This is **cz1993's personal-interest project** — deliberately separate from any company/work
  repositories. Do not attribute anything to a company.
- **All commits and PRs are authored by `cz1993`.** Configure git:
  `user.name = cz1993`, `user.email = 56002317+cz1993@users.noreply.github.com`.
- **Reviewers** may be **Claude** or **CodeX** — name the reviewer explicitly in each PR
  (e.g. a `Reviewer: Claude` / `Reviewer: CodeX` line). The owner (cz1993) authors and merges.

## The no-data rule (critical, zero tolerance)

- **Never** commit real company or personal data, documents, PII, secrets, credentials, API keys,
  tokens, or proprietary files — not in the tree, not in history, ever.
- If you find any such file already present, **remove it immediately**; if it reached git history,
  stop and scrub it (git filter-repo / BFG) **after confirming with the owner**, then force-push.
- Keep the safeguards working: `.gitignore` data/secret patterns, the CI "no-data" scan, and the
  pre-commit hook. Treat a tripped guard as a release blocker.
- **Sample data is allowed and encouraged** — but only (a) synthetic/fictional data you generate,
  or (b) genuinely public, permissively licensed (CC0 / public-domain / CC-BY / MIT) files with
  documented provenance and licence in `examples/DATA_PROVENANCE.md`.

## Protect the differentiators

Lead with these; they are why MirrorArc exists (see `docs/positioning.md`):
the **mirror layer** (Office + GitHub → refreshed markdown mirrors), **governance**
(PII/retention/secrets-out), **anti-proliferation** (consolidate > create), and **linking-first**
retrieval. Do **not** drift back into "another generic LLM-wiki," and do **not** add a vector DB.

## Knowledge-projection rules

- Preserve L0 originals as authority. Generated output must retain stable identity, hashes,
  provenance, lifecycle, and rebuild behavior.
- Each active opaque source normally has one active L1 Markdown projection. Do not duplicate native
  Markdown/text merely to satisfy a file-count rule.
- Relationships are ledger data with evidence and state, not generated notes. L2 synthesis is a
  many-to-few view, ephemeral unless pin/review/audit policy justifies persistence.
- Never silently overwrite a reviewed view. Mark it stale and keep any replacement candidate
  separate until reviewed.
- `INDEX.md`, declared authoritative Markdown, governed L1/L2, and operational controls are the
  allowed durable Markdown categories. Inventory legacy/unknown content before write-mode migration.
- Deterministic correctness cannot depend on a model. Do not introduce a second watcher, lifecycle
  authority, portal database, sync system, or relationship inference path.

## Tech + quality bar

### Local development and final shipment policy

Operator direction (2026-09-18): project development and validation run locally. Hosted GitHub
CI/CD is not a development or acceptance prerequisite. Keep equivalent local quality and no-data
gates; do not weaken tests or safeguards to avoid hosted runs. Do not trigger workflow runs or
make incremental development pushes. Do not change remote branch protections or repository
settings without explicit approval.

For the current trustworthy-context batch, follow
`docs/TRUSTWORTHY_CONTEXT_EXECUTION_PLAN.md`. Development happens in a separate session; the
originating planning session performs post-development review. This project-specific workflow
does not use ADS bilateral CLI review or agent GitHub identities. Preserve owner authorship.
After local completion and planning-session acceptance, ship the approved changes as one
consolidated PR and merge, under the owner. Do not push or merge before that checkpoint. Inspect
CI, Pages, and release triggers before shipment; code shipment must not silently authorize a demo
deployment, package release, or remote-setting change.

- Python 3 (stdlib + PyYAML + markitdown) and POSIX shell. No heavy frameworks; keep deps minimal.
- Cross-platform (macOS + Linux). Scripts must stay **idempotent**.
- Every behavior change: run the package-owned vault lint through the example's tool shim, run
  the test suite, and update `CHANGELOG.md` and relevant docs. Local gates and accepted review,
  rather than hosted CI, govern this project's final shipment. For documentation-only changes,
  check links, diff formatting, template-copy consistency, and no-data safety; do not claim a
  fresh runtime validation.
- Design for users from **many industries**, not one — keep taxonomy/entities/retention
  configurable and the copy jargon-free.
