# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import os
from pathlib import Path
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]


def package_cli_env() -> dict[str, str]:
    env = os.environ.copy()
    src_path = str(ROOT / "src")
    env["PYTHONPATH"] = src_path if not env.get("PYTHONPATH") else f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def test_generate_messy_benchmark_corpus_writes_private_run_artifacts(tmp_path: Path) -> None:
    target = tmp_path / "messy-vault"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_messy_benchmark_corpus.py"),
            "--target",
            str(target),
            "--files",
            "20",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["corpus_files"] == 20
    assert payload["source_files"] == 12
    assert payload["curated_files"] == 8
    assert payload["plain_dump_files"] == 12
    assert payload["tasks"] == 5
    assert payload["comparison_modes"] == [
        "raw_source_folder",
        "plain_markitdown_dump",
        "mirrorarc_markdown",
    ]
    assert payload["result_slots"] == 15

    gitignore = (target / ".gitignore").read_text(encoding="utf-8")
    assert "_benchmark/" in gitignore
    assert (target / "_benchmark" / "MESSY_BENCHMARK_RUN.md").exists()
    assert (target / "_benchmark" / "messy-corpus-summary.json").exists()
    assert len(list((target / "_benchmark" / "plain_markitdown_dump").rglob("*.md"))) == 12

    task_pack = yaml.safe_load((target / "_meta" / "agent-readiness-tasks.yml").read_text(encoding="utf-8"))
    assert task_pack["schema_version"] == 1
    assert task_pack["corpus"] == "messy-synthetic-consulting-corpus"
    assert {task["family"] for task in task_pack["tasks"]} == {
        "answer",
        "audit",
        "consolidate",
        "reconcile",
        "update",
    }
    assert all(task["source_paths"] for task in task_pack["tasks"])
    assert all(task["generated_mirror_paths"] for task in task_pack["tasks"])

    scaffold = yaml.safe_load(
        (target / "_benchmark" / "agent-readiness-results-scaffold.yml").read_text(encoding="utf-8")
    )
    assert len(scaffold["results"]) == 15
    assert all(entry["score"] is None for entry in scaffold["results"])
    assert all(entry["reviewer_corrections"] is None for entry in scaffold["results"])

    benchmark = subprocess.run(
        [
            sys.executable,
            "-m",
            "mirrorarc.cli",
            "--root",
            str(target),
            "benchmark",
            "--json",
        ],
        cwd=ROOT,
        env=package_cli_env(),
        text=True,
        capture_output=True,
    )

    assert benchmark.returncode == 0, benchmark.stderr or benchmark.stdout
    benchmark_payload = json.loads(benchmark.stdout)
    assert benchmark_payload["summary"]["tasks"] == 5
    assert benchmark_payload["summary"]["source_paths"] == 25
    assert benchmark_payload["summary"]["generated_mirror_paths"] == 25
    assert benchmark_payload["result_summary"] == {}
    assert benchmark_payload["errors"] == []
    assert "NW-MESSY" not in benchmark.stdout


def test_generate_messy_benchmark_corpus_reviewed_results_validate_after_sync(tmp_path: Path) -> None:
    target = tmp_path / "messy-vault"

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_messy_benchmark_corpus.py"),
            "--target",
            str(target),
            "--files",
            "20",
            "--write-reviewed-results",
            "--json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["reviewed_result_pack"] == "_benchmark/agent-readiness-results-reviewed.yml"

    sync = subprocess.run(
        [
            sys.executable,
            "-m",
            "mirrorarc.cli",
            "--root",
            str(target),
            "sync",
            "--json",
        ],
        cwd=ROOT,
        env=package_cli_env(),
        text=True,
        capture_output=True,
    )

    assert sync.returncode == 0, sync.stderr or sync.stdout

    benchmark = subprocess.run(
        [
            sys.executable,
            "-m",
            "mirrorarc.cli",
            "--root",
            str(target),
            "benchmark",
            "--results",
            "_benchmark/agent-readiness-results-reviewed.yml",
            "--require-results",
            "--require-citations",
            "--require-prompt-safety",
            "--json",
        ],
        cwd=ROOT,
        env=package_cli_env(),
        text=True,
        capture_output=True,
    )

    assert benchmark.returncode == 0, benchmark.stderr or benchmark.stdout
    benchmark_payload = json.loads(benchmark.stdout)
    assert benchmark_payload["errors"] == []
    assert benchmark_payload["warnings"] == []
    assert benchmark_payload["result_summary"]["results"] == 15
    modes = benchmark_payload["result_summary"]["modes"]
    assert modes["raw_source_folder"]["score"] == 3
    assert modes["raw_source_folder"]["max_score"] == 10
    assert modes["raw_source_folder"]["reviewer_corrections"] == 10
    assert modes["plain_markitdown_dump"]["score"] == 4
    assert modes["plain_markitdown_dump"]["max_score"] == 10
    assert modes["plain_markitdown_dump"]["reviewer_corrections"] == 8
    assert modes["mirrorarc_markdown"]["score"] == 10
    assert modes["mirrorarc_markdown"]["max_score"] == 10
    assert modes["mirrorarc_markdown"]["reviewer_corrections"] == 0
    assert modes["mirrorarc_markdown"]["generated_mirror_citations"] == 5
    assert "NW-MESSY" not in benchmark.stdout


def test_generate_messy_benchmark_corpus_rejects_source_checkout_target() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_messy_benchmark_corpus.py"),
            "--target",
            str(ROOT),
            "--force",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "outside the MirrorArc source checkout" in result.stderr


def test_generate_messy_benchmark_corpus_rejects_broad_force_target() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_messy_benchmark_corpus.py"),
            "--target",
            str(Path.home()),
            "--force",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 1
    assert "too broad to replace safely" in result.stderr
