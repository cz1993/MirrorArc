# SPDX-License-Identifier: AGPL-3.0-or-later
import os
import subprocess
import sys
from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
RELEASE_WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"
RELEASE_DOC = ROOT / "docs" / "RELEASE.md"
KICKOFF_PROMPT = ROOT / "docs" / "CODEX_KICKOFF_PROMPT.md"
FINISH_LINE = ROOT / "docs" / "V1_FINISH_LINE.md"
HISTORICAL_PLANNING_DOCS = (
    ROOT / "docs" / "VAULTWRIGHT_WHITEPAPER_2026-06-23.md",
    ROOT / "docs" / "revisions" / "VAULTWRIGHT_WHITEPAPER_2026-06-24.md",
    ROOT / "docs" / "VAULTWRIGHT_CODEX_MEGA_PROMPT_2026-06-24.md",
    ROOT / "docs" / "V1_PROGRESS_AUDIT_2026-06-23.md",
)
PYPROJECT = ROOT / "pyproject.toml"


def test_docs_pin_package_first_onboarding_commands() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    quickstart = (ROOT / "docs" / "quickstart.md").read_text(encoding="utf-8")

    for text in (readme, quickstart):
        assert "Python 3.11+" in text
        assert (
            "uvx --from git+https://github.com/cz1993/vaultwright.git vaultwright init "
            "--profile business-operations ~/my-business-vault"
        ) in text
        assert (
            "pipx run --spec git+https://github.com/cz1993/vaultwright.git vaultwright init "
            "--profile business-operations ~/my-business-vault"
        ) in text
        assert "uvx vaultwright init --profile business-operations ~/my-business-vault" in text
        assert "pipx run vaultwright init --profile business-operations ~/my-business-vault" in text
        assert "uv tool install git+https://github.com/cz1993/vaultwright.git" in text
        assert "pipx install git+https://github.com/cz1993/vaultwright.git" in text
        assert "vaultwright --version" in text
        assert "git clone https://github.com/cz1993/vaultwright.git vaultwright" in text


def test_kickoff_prompt_routes_future_work_to_stage3_validation() -> None:
    text = KICKOFF_PROMPT.read_text(encoding="utf-8")

    assert "Stage 0, Stage 1A, Stage 1B, and Stage 2 are closed." in text
    assert "Stage 3 external validation is the next gate" in text
    assert "docs/VALIDATION_GATE.md" in text
    assert "docs/STAGE3_VALIDATION_STATUS.md" in text
    assert "docs/DESIGN_PARTNER_RECRUITING.md" in text
    assert "docs/FIRST_EXTERNAL_PILOT_RUNBOOK.md" in text
    assert "Do not start Obsidian adapter, generated Canvas, evidence index, Explorer" in text
    assert "Docling/email/connectors, visualization, or new report surfaces" in text
    assert "Work Stage 1 package/profile convergence before adding broad examples" not in text
    assert "The sample-data hunt (do this in goal-pursuing mode)" not in text


def test_historical_planning_docs_are_marked_superseded() -> None:
    finish_line = FINISH_LINE.read_text(encoding="utf-8")

    assert "Current execution order is controlled by this matrix" in finish_line
    assert "docs/VALIDATION_GATE.md" in finish_line
    assert "Current progress and next execution order are summarized in" not in finish_line

    for path in HISTORICAL_PLANNING_DOCS:
        text = path.read_text(encoding="utf-8")
        assert "Historical" in text
        assert "not the current" in text
        assert "Stage 3 external validation" in text
        assert "docs/VALIDATION_GATE.md" in text


def test_release_workflow_is_tag_only_and_draft_prerelease() -> None:
    text = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert "tags:" in text
    assert '"v*"' in text
    assert "branches:" not in text
    assert "gh release create" in text
    assert "--draft" in text
    assert "--prerelease" in text


def test_release_checklist_tag_matches_package_version() -> None:
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    version = pyproject["project"]["version"]
    init_text = (ROOT / "src" / "vaultwright" / "__init__.py").read_text(encoding="utf-8")
    text = RELEASE_DOC.read_text(encoding="utf-8")

    assert version == "0.1.0a1"
    assert f'__version__ = "{version}"' in init_text
    assert f"git tag -a v{version} -m \"v{version}\"" in text
    assert f"git push origin v{version}" in text


def test_cli_global_version_outputs_package_version() -> None:
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    version = pyproject["project"]["version"]
    env = os.environ.copy()
    src_path = str(ROOT / "src")
    env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}{os.pathsep}{env['PYTHONPATH']}"

    result = subprocess.run(
        [sys.executable, "-m", "vaultwright.cli", "--version"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"vaultwright {version}"


def test_external_pilot_docs_start_with_installed_command_smoke_check() -> None:
    runbook = (ROOT / "docs" / "FIRST_EXTERNAL_PILOT_RUNBOOK.md").read_text(encoding="utf-8")
    worksheet = (ROOT / "docs" / "PILOT_WORKSHEET.md").read_text(encoding="utf-8")

    assert "## Operator Environment Smoke Test" in runbook
    assert "command -v vaultwright" in runbook
    assert "vaultwright --version" in runbook
    assert "vaultwright profile list" in runbook
    assert "Do not spend participant time debugging Python packaging." in runbook
    assert "vaultwright --version" in worksheet
    assert "vaultwright profile list" in worksheet


def test_workflows_use_current_action_majors() -> None:
    ci = CI_WORKFLOW.read_text(encoding="utf-8")
    release = RELEASE_WORKFLOW.read_text(encoding="utf-8")
    combined = f"{ci}\n{release}"

    assert "actions/checkout@v7" in combined
    assert "actions/setup-python@v6" in combined
    assert "actions/upload-artifact@v7" in release
    assert "actions/download-artifact@v8" in release
    assert "actions/checkout@v4" not in combined
    assert "actions/setup-python@v5" not in combined
    assert "actions/upload-artifact@v4" not in combined
    assert "actions/download-artifact@v4" not in combined


def test_cli_help_marks_review_plan_experimental_surfaces() -> None:
    env = os.environ.copy()
    src_path = str(ROOT / "src")
    env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
    result = subprocess.run(
        [sys.executable, "-m", "vaultwright.cli", "--help"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    benchmark = subprocess.run(
        [sys.executable, "-m", "vaultwright.cli", "benchmark", "--help"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert benchmark.returncode == 0, benchmark.stderr
    help_text = " ".join(result.stdout.split())
    benchmark_help = " ".join(benchmark.stdout.split())
    for command in ("overlap", "conversion", "pilot", "m365", "sandbox"):
        assert command in result.stdout
    assert "[experimental] Print a read-only overlap threshold calibration report." in help_text
    assert "[experimental] Print a read-only conversion spot-check report." in help_text
    assert "[experimental] Print a read-only design-partner pilot evidence report." in help_text
    assert "[experimental] Print a read-only Microsoft 365/Copilot handoff report." in help_text
    assert "[experimental] Print a read-only copied-vault sandbox readiness report." in help_text
    assert "experimental scaffold helpers remain unstable" in help_text
    assert "[experimental] Create a private benchmark task scaffold." in benchmark_help
    assert "[experimental] Print a private benchmark run worksheet." in benchmark_help


def test_release_workflow_verifies_built_wheel_before_release() -> None:
    text = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert "python -m build" in text
    assert "dist/vaultwright-*.whl" in text
    assert "vaultwright-release-venv" in text
    assert "vaultwright\" init" in text
    assert "test -f \"$tmp_vault/tools/catalog_report.py\"" in text
    assert "test -f \"$tmp_vault/tools/m365_report.py\"" in text
    assert "test -f \"$tmp_vault/tools/overlap_report.py\"" in text
    assert "test -f \"$tmp_vault/tools/review_ledger.py\"" in text
    assert "catalog --check" in text
    assert "catalog --html --check" in text
    assert "profile diff 0.1.0" in text
    assert "profile migrate --plan" in text
    assert "profile migrate --write --json" in text
    assert "profile views --check" in text
    assert "migrate annotations --plan" in text
    assert "--root \"$tmp_vault\" doctor --json" in text
    assert "--root \"$tmp_vault\" lint" in text
    assert "--root \"$tmp_vault\" plan" in text
    assert "--root \"$tmp_vault\" sync" in text
    assert "--root \"$tmp_vault\" sync --json" in text
    assert "--root \"$tmp_vault\" status" in text
    assert "--root \"$tmp_vault\" status --json" in text
    assert "test -f \"$tmp_vault/tools/sandbox_report.py\"" in text
    assert "sandbox --source-root" in text
    assert "conversion --guide --json" in text
    assert "conversion --init-results" in text
    assert "conversion --results _meta/conversion-quality-results.yml --require-reviewed --json" in text
    assert "release-smoke-source" in text
    assert "agent-readiness-results.yml" in text
    assert "--require-prompt-safety" in text
    assert "overlap --json" in text
    assert "overlap --worksheet" in text
    assert "m365 --json" in text
    assert "review --artifact CATALOG.html --status approved --reviewer Release --json" in text
    assert "review --check" in text
    assert "migration --worksheet" in text
    assert "migration --runbook" in text
    assert "migration --normalize-frontmatter-domains --worksheet" in text
    assert "pilot --worksheet" in text
    assert "recovery --worksheet" in text
    assert "actions/upload-artifact@v7" in text


def test_ci_workflow_smokes_sandbox_command() -> None:
    text = CI_WORKFLOW.read_text(encoding="utf-8")

    assert "src/vaultwright/catalog.py" in text
    assert "src/vaultwright/benchmark.py" in text
    assert "src/vaultwright/conversion.py" in text
    assert "src/vaultwright/doctor.py" in text
    assert "src/vaultwright/m365.py" in text
    assert "src/vaultwright/migration.py" in text
    assert "src/vaultwright/overlap.py" in text
    assert "src/vaultwright/pilot.py" in text
    assert "src/vaultwright/recovery.py" in text
    assert "src/vaultwright/review_ledger.py" in text
    assert "src/vaultwright/runtime_profile.py" in text
    assert "src/vaultwright/sandbox.py" in text
    assert "src/vaultwright/views.py" in text
    assert "src/vaultwright/annotation_migration.py" in text
    assert "src/vaultwright/profile_migration.py" in text
    assert "template/tools/catalog_report.py" in text
    assert "template/tools/m365_report.py" in text
    assert "template/tools/overlap_report.py" in text
    assert "template/tools/review_ledger.py" in text
    assert "test -f \"$tmp_vault/tools/catalog_report.py\"" in text
    assert "test -f \"$tmp_vault/tools/m365_report.py\"" in text
    assert "test -f \"$tmp_vault/tools/overlap_report.py\"" in text
    assert "test -f \"$tmp_vault/tools/review_ledger.py\"" in text
    assert "catalog --check" in text
    assert "catalog --html --check" in text
    assert "profile diff 0.1.0" in text
    assert "profile migrate --plan" in text
    assert "profile migrate --write --json" in text
    assert "profile views --check" in text
    assert "migrate annotations --plan" in text
    assert "--root \"$tmp_vault\" doctor" in text
    assert "--root \"$tmp_vault\" doctor --json" in text
    assert "--root \"$tmp_vault\" lint" in text
    assert "--root \"$tmp_vault\" plan" in text
    assert "--root \"$tmp_vault\" sync" in text
    assert "--root \"$tmp_vault\" sync --json" in text
    assert "--root \"$tmp_vault\" status" in text
    assert "--root \"$tmp_vault\" status --json" in text
    assert "template/tools/sandbox_report.py" in text
    assert "test -f \"$tmp_vault/tools/sandbox_report.py\"" in text
    assert "sandbox --source-root" in text
    assert "conversion --init-results" in text
    assert "conversion --results _meta/conversion-quality-results.yml --require-reviewed --json" in text
    assert "release-smoke-source" in text
    assert "agent-readiness-results.yml" in text
    assert "--require-prompt-safety" in text
    assert "migration --worksheet" in text
    assert "migration --runbook" in text
    assert "migration --normalize-frontmatter-domains --worksheet" in text
    assert "overlap --json" in text
    assert "overlap --worksheet" in text
    assert "m365 --json" in text
    assert "review --artifact CATALOG.md --status approved --reviewer CI --json" in text
    assert "review --artifact CATALOG.html --status approved --reviewer CI --json" in text
    assert "review --check" in text
    assert "recovery --json" in text
    assert "recovery --worksheet" in text


def test_release_workflow_isolates_write_token_to_publish_job() -> None:
    text = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert "persist-credentials: false" in text
    assert "publish-draft:" in text
    assert "needs: build-release" in text
    assert "actions/download-artifact@v8" in text
    assert "contents: read" in text
    assert "contents: write" in text
    assert text.index("contents: write") > text.index("publish-draft:")
    assert text.index("GH_TOKEN: ${{ github.token }}") > text.index("publish-draft:")
    assert text.index("GH_REPO: ${{ github.repository }}") > text.index("publish-draft:")


def test_release_workflow_refuses_to_mutate_published_release() -> None:
    text = RELEASE_WORKFLOW.read_text(encoding="utf-8")

    assert "--json isDraft,isPrerelease" in text
    assert "not both draft and prerelease" in text
    assert "refusing to clobber assets" in text
    assert "gh release upload" in text
    assert "--clobber" in text


def test_release_workflow_does_not_publish_to_pypi() -> None:
    text = RELEASE_WORKFLOW.read_text(encoding="utf-8").lower()

    forbidden = [
        "pypi",
        "twine upload",
        "__token__",
        "id-token: write",
        "trusted publishing",
    ]
    assert not any(value in text for value in forbidden)


def test_release_checklist_documents_owner_review_and_limitations() -> None:
    text = RELEASE_DOC.read_text(encoding="utf-8")

    assert "draft, prerelease GitHub Release" in text
    assert "owner should publish it only after reviewing" in text
    assert "This repository does not publish to PyPI yet." in text
    assert "`sandbox`" in text
    assert "conversion quality" in text
    assert "conversion-quality result packs" in text
    assert "external pilot evidence" in text
