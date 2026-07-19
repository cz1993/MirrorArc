# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "create_plain_markitdown_dump.py"


def test_plain_markitdown_dump_creates_private_baseline_from_copied_vault(tmp_path: Path) -> None:
    vault = tmp_path / "messy-vault"
    generated = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_messy_benchmark_corpus.py"),
            "--target",
            str(vault),
            "--files",
            "20",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert generated.returncode == 0, generated.stderr or generated.stdout
    shutil.rmtree(vault / "_benchmark" / "plain_markitdown_dump")

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--root",
            str(vault),
            "--force",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload == {
        "converted": 12,
        "errors": 0,
        "output_root": "_benchmark/plain_markitdown_dump",
        "summary_path": "_benchmark/plain_markitdown_dump-summary.json",
    }
    dumps = sorted((vault / "_benchmark" / "plain_markitdown_dump").rglob("*.md"))
    assert len(dumps) == 12
    sample = dumps[0].read_text(encoding="utf-8")
    assert "# Plain MarkItDown Dump" in sample
    assert "No MirrorArc manifest identity" in sample
    assert "NW-MESSY" in sample

    summary = json.loads((vault / "_benchmark" / "plain_markitdown_dump-summary.json").read_text(encoding="utf-8"))
    assert summary["schema_version"] == 1
    assert summary["converted"] == 12
    assert summary["errors"] == 0
    assert len(summary["records"]) == 12
    assert all(record["status"] == "converted" for record in summary["records"])


def test_plain_markitdown_dump_refuses_existing_output_without_force(tmp_path: Path) -> None:
    vault = tmp_path / "messy-vault"
    generated = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_messy_benchmark_corpus.py"),
            "--target",
            str(vault),
            "--files",
            "20",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert generated.returncode == 0, generated.stderr or generated.stdout

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(vault)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "already exists; use --force" in result.stderr


def test_plain_markitdown_dump_refuses_source_checkout_root() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(ROOT / "examples" / "government-services-vault")],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "refusing to write private benchmark output inside the MirrorArc source checkout" in result.stderr
