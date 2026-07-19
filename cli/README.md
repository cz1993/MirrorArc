# MirrorArc CLI

The vault-local wrapper exists today as `template/tools/mirrorarc.py` and is copied into new
vaults. The source-installable console entry point is defined in `pyproject.toml` as
`mirrorarc = mirrorarc.cli:main`.

Current wrapper commands:

| Command | Does |
| --- | --- |
| `python3.11 tools/mirrorarc.py init <dir>` | scaffold a vault when run from the repo checkout |
| `python3.11 tools/mirrorarc.py plan` | inventory source files and proposed mirror actions without writing |
| `python3.11 tools/mirrorarc.py sync` | run the Office + GitHub repo mirror syncs |
| `python3.11 tools/mirrorarc.py status` | report manifest-backed clean, stale, missing, conflicted, and unsupported states |
| `python3.11 tools/mirrorarc.py recovery` | print a read-only recovery checklist from source/repo manifests |
| `python3.11 tools/mirrorarc.py lint` | run the vault health check |
| `python3.11 tools/mirrorarc.py benchmark` | validate `_meta/agent-readiness-tasks.yml`; add `--require-generated` after sync |
| `python3.11 tools/mirrorarc.py doctor` | read-only preflight for required files/tools, Python dependencies, manifest lifecycle counts, sync audit presence, git backup posture, and GitHub auth posture |

Use `--root <vault-dir>` before the subcommand to operate on another vault that has its own
`tools/` directory, for example `python3.11 tools/mirrorarc.py --root ~/client-vault plan`.

For source/development installs:

```bash
python3.11 -m pip install -e .
mirrorarc --root ~/client-vault plan
mirrorarc --root ~/client-vault benchmark
mirrorarc --root ~/client-vault recovery
mirrorarc init ~/new-vault
```

`mirrorarc init` copies the packaged template. Set `MIRRORARC_REPO` only when you intentionally
want to scaffold from a specific source checkout template instead.

Design notes:
- Keep it dependency-light (Python stdlib + PyYAML + markitdown).
- The wrapper calls the existing scripts as the source of truth; do not fork sync/lint logic.
- `doctor` is a preflight signal, not a substitute for `plan`, `status`, `lint`, backups, or human
  review before source moves/deletions.
- Future release packaging should keep these commands delegating to vault-local tools unless the
  underlying sync/lint implementations are intentionally moved into the package.
