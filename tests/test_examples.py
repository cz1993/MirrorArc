# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path
import os
import shutil
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "ontario-grid-evidence-vault"
OFFICE_SOURCE_EXTS = {".docx", ".pptx", ".xlsx", ".pdf"}
DISALLOWED_DATA_EXTS = OFFICE_SOURCE_EXTS | {".csv"}
EXPECTED_OFFICE_SOURCES = {
    Path("10_context/briefs/ontario-grid-project-charter.docx"),
    Path("20_sources/briefs/ontario-grid-source-assessment.docx"),
    Path("20_sources/workbooks/open-data-inventory.xlsx"),
    Path("50_analysis/workbooks/historical-demand-profile.xlsx"),
    Path("50_analysis/workbooks/ontario-grid-evidence-scorecard.xlsx"),
    Path("60_models/workbooks/illustrative-model-evaluation.xlsx"),
    Path("70_outputs/briefings/evidence-governance-review.pptx"),
    Path("70_outputs/briefings/ontario-grid-evidence-briefing.pptx"),
    Path("70_outputs/reports/ontario-grid-evidence-methodology.pdf"),
    Path("70_outputs/reports/ontario-grid-evidence-pack.pdf"),
    Path("80_governance/briefs/public-corpus-governance-memo.docx"),
    Path("90_operations/briefs/data-quality-incident-review.docx"),
}
EXPECTED_GENERATED = {
    Path("_meta/source-manifest.json"),
    Path("_meta/repo-manifest.json"),
    Path("_meta/sync-audit.jsonl"),
    Path("20_sources/repos/ontario-grid-evidence-pipeline.md"),
    *(Path("_mirrors") / source.with_suffix(".md") for source in EXPECTED_OFFICE_SOURCES),
}
OGL_SOURCE_DIR = Path("20_sources/open-data/ontario-energy-report-2023")
EXPECTED_OGL_CSVS = {
    "exports-gwh.csv",
    "forecast-demand-peaks.csv",
    "generation-emissions-intensity.csv",
    "generation-output-by-fuel-type-grid-connected-gwh.csv",
    "generation-output-by-fuel-type-grid-connected-percent.csv",
    "greenhouse-gas-emissions-ontario-electricity.csv",
    "historical-annual-ontario-energy-demand-twh.csv",
    "historical-monthly-generation-output-by-fuel-type-mwh.csv",
    "historical-monthly-ontario-demand-peaks-minimums-mw.csv",
    "imports-gwh.csv",
    "ontario-demand-peaks-minimums-mw.csv",
    "ontario-peak-demand-mw.csv",
}
COPIED_TOOL_FILES = {
    path.relative_to(ROOT / "template" / "tools").as_posix()
    for path in (ROOT / "template" / "tools").rglob("*")
    if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
}


def source_payloads(vault: Path) -> dict[Path, bytes]:
    payloads: dict[Path, bytes] = {}
    for path in vault.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(vault)
        if path.suffix.lower() in OFFICE_SOURCE_EXTS and "_mirrors" not in rel.parts:
            payloads[rel] = path.read_bytes()
        elif rel.parts[:2] == ("_fixtures", "repos"):
            payloads[rel] = path.read_bytes()
    return payloads


def generated_payloads(vault: Path) -> dict[Path, bytes]:
    return {
        rel: (vault / rel).read_bytes()
        for rel in EXPECTED_GENERATED
        if rel.name != "sync-audit.jsonl"
    }


def assert_no_generated_residue(vault: Path) -> None:
    assert not [
        path
        for path in (vault / "_mirrors").rglob("*")
        if path.is_file() and path.name != ".gitkeep"
    ]
    assert not [
        path
        for path in (vault / "_meta").glob("*")
        if path.name.endswith("-manifest.json") or path.name == "sync-audit.jsonl"
    ]
    assert not list((vault / "20_sources" / "repos").glob("*.md"))


def run_cli(vault: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    src_path = str(ROOT / "src")
    env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
    return subprocess.run(
        [sys.executable, str(vault / "tools" / "mirrorarc.py"), *args],
        cwd=vault,
        text=True,
        capture_output=True,
        env=env,
    )


def test_flagship_example_source_tree_has_no_generated_residue() -> None:
    assert_no_generated_residue(EXAMPLE)
    assert all(not (EXAMPLE / rel).exists() for rel in EXPECTED_GENERATED)
    assert "sync |" not in (EXAMPLE / "log.md").read_text(encoding="utf-8")


def test_flagship_example_is_a_substantial_data_product_workspace() -> None:
    excluded_roots = {"tools", "_meta", "_templates", ".obsidian", "_mirrors"}
    meaningful = [
        path
        for path in EXAMPLE.rglob("*")
        if path.is_file()
        and path.name != ".gitkeep"
        and not excluded_roots.intersection(path.relative_to(EXAMPLE).parts)
    ]
    assert len(meaningful) >= 50

    profile = yaml.safe_load((EXAMPLE / "_meta" / "profile.yml").read_text(encoding="utf-8"))
    assert profile["id"] == "data-product"
    assert set(profile["domains"]) == {
        "inbox",
        "context",
        "sources",
        "contracts",
        "pipelines",
        "analysis",
        "models",
        "outputs",
        "governance",
        "operations",
    }
    assert (EXAMPLE / "INDEX.md").is_file()
    assert (EXAMPLE / "_meta" / "agent-rules.md").is_file()


def test_flagship_example_tool_copies_match_template() -> None:
    for rel in COPIED_TOOL_FILES:
        assert (EXAMPLE / "tools" / rel).read_bytes() == (ROOT / "template" / "tools" / rel).read_bytes(), rel


def test_public_source_selection_and_boundary_are_explicit() -> None:
    csvs = {path.name for path in (EXAMPLE / OGL_SOURCE_DIR).glob("*.csv")}
    notes = {path.name for path in (EXAMPLE / OGL_SOURCE_DIR).glob("*-notes-en.txt")}
    assert csvs == EXPECTED_OGL_CSVS
    assert len(notes) == len(EXPECTED_OGL_CSVS)

    source_readme = (EXAMPLE / OGL_SOURCE_DIR / "README.md").read_text(encoding="utf-8")
    assert "Open Government Licence" in source_readme
    assert "2df0e2aec3b4c11103ee2fe67dbdb4e7fb344f0d6228ccb378bcc036bb9e956a" in source_readme

    reference_notes = list((EXAMPLE / "20_sources").glob("*.md"))
    assert reference_notes
    ieso_notes = [path for path in reference_notes if "ieso" in path.as_posix().lower() or "ieso.ca" in path.read_text(encoding="utf-8").lower()]
    assert len(ieso_notes) >= 5
    for path in ieso_notes:
        text = path.read_text(encoding="utf-8")
        assert "license: reference-only" in text
        assert "https://www.ieso.ca/" in text
        assert "metadata" in text.lower() or "reference" in text.lower()

    ieso_binaries = [
        path
        for path in EXAMPLE.rglob("*")
        if path.is_file() and "ieso" in path.name.lower() and path.suffix.lower() != ".md"
    ]
    assert ieso_binaries == []


def test_all_committed_data_and_office_artifacts_are_provenanced() -> None:
    provenance = (ROOT / "examples" / "DATA_PROVENANCE.md").read_text(encoding="utf-8")
    committed = {
        path.relative_to(ROOT).as_posix()
        for path in EXAMPLE.rglob("*")
        if path.is_file() and path.suffix.lower() in DISALLOWED_DATA_EXTS
    }
    expected = {f"`{rel}`" for rel in committed}
    missing = sorted(path for path in expected if path not in provenance)
    assert not missing
    assert {path.relative_to(EXAMPLE) for path in EXAMPLE.rglob("*") if path.is_file() and path.suffix.lower() in OFFICE_SOURCE_EXTS} == EXPECTED_OFFICE_SOURCES


def test_synthetic_repo_fixture_is_independent_and_green() -> None:
    fixture = EXAMPLE / "_fixtures" / "repos" / "ontario-grid-evidence-pipeline"
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=fixture,
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(fixture / "src")},
    )
    assert result.returncode == 0, result.stderr or result.stdout
    fixture_text = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in fixture.rglob("*")
        if path.is_file()
    )
    assert "synthetic" in fixture_text.lower()
    assert "MAPE" in fixture_text
    assert "5" in fixture_text


def test_flagship_example_regenerates_idempotently_without_mutating_sources(tmp_path: Path) -> None:
    vault = tmp_path / "ontario-grid-evidence-vault"
    shutil.copytree(EXAMPLE, vault)
    before_sources = source_payloads(vault)

    plan = run_cli(vault, "plan")
    assert plan.returncode == 0, plan.stderr or plan.stdout
    assert_no_generated_residue(vault)

    first = run_cli(vault, "sync")
    assert first.returncode == 0, first.stderr or first.stdout
    for rel in EXPECTED_GENERATED:
        assert (vault / rel).is_file(), rel
    assert source_payloads(vault) == before_sources
    first_generated = generated_payloads(vault)

    status = run_cli(vault, "status")
    assert status.returncode == 0, status.stderr or status.stdout
    lint = run_cli(vault, "lint")
    assert lint.returncode == 0, lint.stderr or lint.stdout

    second = run_cli(vault, "sync")
    assert second.returncode == 0, second.stderr or second.stdout
    assert source_payloads(vault) == before_sources
    assert generated_payloads(vault) == first_generated


def test_private_overlay_is_ignored_and_absent() -> None:
    assert not (EXAMPLE / "_private-overlay").exists()
    ignore = (EXAMPLE / ".gitignore").read_text(encoding="utf-8")
    assert "_private-overlay/" in ignore


def test_legacy_examples_are_gone() -> None:
    assert not (ROOT / "examples" / "northwind-robotics-vault").exists()
    assert not (ROOT / "examples" / "government-services-vault").exists()
