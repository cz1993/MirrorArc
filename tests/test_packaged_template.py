# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_TEMPLATE = ROOT / "template"
PACKAGE_TEMPLATE = ROOT / "src" / "noeticweave" / "template"
PACKAGE_OWNED_TOOL_MODULES = {
    "benchmark_tasks.py": ("noeticweave.benchmark", True),
    "catalog_report.py": ("noeticweave.catalog", True),
    "conversion_report.py": ("noeticweave.conversion", True),
    "lint_vault.py": ("noeticweave.lint", False),
    "m365_report.py": ("noeticweave.m365", True),
    "migration_report.py": ("noeticweave.migration", True),
    "overlap_report.py": ("noeticweave.overlap", True),
    "pilot_report.py": ("noeticweave.pilot", True),
    "recovery_report.py": ("noeticweave.recovery", True),
    "review_ledger.py": ("noeticweave.review_ledger", True),
    "sandbox_report.py": ("noeticweave.sandbox", True),
    "noeticweave.py": ("noeticweave.cli", False),
}


def generated_cache(path: Path) -> bool:
    return "__pycache__" in path.parts or path.suffix == ".pyc"


def template_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not generated_cache(path)
    }


def test_packaged_template_matches_repository_template() -> None:
    source_files = template_files(SOURCE_TEMPLATE)
    package_files = template_files(PACKAGE_TEMPLATE)

    assert package_files == source_files
    assert ".gitignore" in package_files
    assert "tools/catalog_report.py" in package_files
    assert "tools/conversion_report.py" in package_files
    assert "tools/m365_report.py" in package_files
    assert "tools/migration_report.py" in package_files
    assert "tools/overlap_report.py" in package_files
    assert "tools/pilot_report.py" in package_files
    assert "tools/recovery_report.py" in package_files
    assert "tools/review_ledger.py" in package_files
    assert "tools/sandbox_report.py" in package_files
    assert "80_sources/repos/.gitkeep" in package_files


def test_package_owned_template_tools_are_shims() -> None:
    for script, (module, reexports_symbols) in PACKAGE_OWNED_TOOL_MODULES.items():
        text = (SOURCE_TEMPLATE / "tools" / script).read_text(encoding="utf-8")

        if reexports_symbols:
            assert f"from {module} import *" in text
        imports_package_main = (
            f"from {module} import main as _package_main" in text
            or f"from {module} import main" in text
        )
        assert imports_package_main
        assert "Missing NoeticWeave package runtime" in text
