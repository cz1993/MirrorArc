# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import pytest
import yaml

from mirrorarc.catalog import build_report, render_html
from mirrorarc.cli import main
from mirrorarc.code_intelligence.adapter import (
    CodeGraphAdapter,
    normalize_affected,
    normalize_files,
    normalize_impact,
    normalize_query,
    normalize_status,
)
from mirrorarc.code_intelligence.context import build_dynamic_code_context, freeze_code_context
from mirrorarc.code_intelligence.service import (
    CACHE_ROOT,
    analyze_repository,
    catalog_report as code_intelligence_catalog_report,
    doctor_report,
    status_report,
)
from mirrorarc.context_assembly.builder import resolve_dynamic_context
from mirrorarc.context_assembly.store import ContextStore

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "codegraph_v1_5_0"
REPO_FIXTURE = ROOT / "examples" / "ontario-electricity-evidence-vault" / "_fixtures" / "repos" / "ontario-electricity-evidence-pipeline"


def fixture(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def copy_vault(tmp_path: Path) -> tuple[Path, str]:
    vault = tmp_path / "vault"
    shutil.copytree(ROOT / "template", vault)
    repository = vault / "_fixtures" / "repos" / "pipeline"
    repository.parent.mkdir(parents=True)
    shutil.copytree(REPO_FIXTURE, repository)
    (vault / "tools" / "repos.yml").write_text(
        "settings:\n  notes_dir: 20_sources/repos\nrepos:\n"
        "  - repo: local/pipeline\n"
        "    local_path: _fixtures/repos/pipeline\n"
        "    note: pipeline.md\n",
        encoding="utf-8",
    )
    from mirrorarc.mirrors.github_repos import repo_id_for

    return vault, repo_id_for("local/pipeline", "pipeline.md")


def fake_codegraph(tmp_path: Path) -> Path:
    binary = tmp_path / "codegraph"
    binary.write_text(
        f"#!{sys.executable}\n"
        "import json, os, pathlib, sys\n"
        f"fixtures = pathlib.Path({str(FIXTURES)!r})\n"
        "args = sys.argv[1:]\n"
        "def emit(name): print((fixtures / name).read_text())\n"
        "if args == ['--version']:\n"
        "    print(os.environ.get('FAKE_CODEGRAPH_VERSION', '1.5.0')); raise SystemExit(0)\n"
        "command = args[0] if args else ''\n"
        "if os.environ.get('FAKE_CODEGRAPH_FAIL') and command == 'files':\n"
        "    print('synthetic provider failure', file=sys.stderr); raise SystemExit(7)\n"
        "project = pathlib.Path(args[1] if command in {'status','init','sync','index'} else args[args.index('--path') + 1])\n"
        "marker = project / '.codegraph' / 'fake-index'\n"
        "if command in {'init','sync','index'}:\n"
        "    marker.parent.mkdir(parents=True, exist_ok=True); marker.write_text('local cache')\n"
        "    print('ok'); raise SystemExit(0)\n"
        "if command == 'status':\n"
        "    if not marker.exists():\n"
        "        print(json.dumps({'initialized': False, 'version': '1.5.0', 'projectPath': str(project), 'indexPath': str(project / '.codegraph'), 'lastIndexed': None})); raise SystemExit(0)\n"
        "    emit('status-current.json'); raise SystemExit(0)\n"
        "if command == 'files': emit('files.json'); raise SystemExit(0)\n"
        "if command == 'query': emit('query-summary.json' if args[1] == 'summary' else 'query-demand-change.json'); raise SystemExit(0)\n"
        "if command == 'callers': emit('callers-demand-change.json'); raise SystemExit(0)\n"
        "if command == 'callees': emit('callees-demand-change.json'); raise SystemExit(0)\n"
        "if command == 'impact': emit('impact-demand-change.json'); raise SystemExit(0)\n"
        "if command == 'affected': emit('affected-summary.json'); raise SystemExit(0)\n"
        "print('unsupported fake command', file=sys.stderr); raise SystemExit(2)\n",
        encoding="utf-8",
    )
    binary.chmod(0o755)
    return binary


def test_recorded_codegraph_contracts_normalize_and_exclude_runtime_timestamps() -> None:
    current = normalize_status(fixture("status-current.json"))
    stale = normalize_status(fixture("status-stale.json"))
    assert current["version"] == "1.5.0"
    assert current["pending_changes"] == {"added": 0, "modified": 0, "removed": 0}
    assert stale["pending_changes"]["modified"] == 1
    assert normalize_query(fixture("query-demand-change.json"))[0]["path"] == "src/grid_evidence/summary.py"
    assert normalize_impact(fixture("impact-demand-change.json"))["affected"][1]["path"] == "tests/test_summary.py"
    assert normalize_affected(fixture("affected-summary.json"))["affected_tests"] == []
    assert normalize_files(fixture("files.json"))[0]["path"] == "src/grid_evidence/summary.py"


def test_adapter_sets_privacy_environment_and_initializes_only_snapshot(tmp_path: Path, monkeypatch) -> None:
    binary = fake_codegraph(tmp_path)
    project = tmp_path / "snapshot"
    project.mkdir()
    adapter = CodeGraphAdapter(binary)
    assert adapter.environment["DO_NOT_TRACK"] == "1"
    assert adapter.environment["CODEGRAPH_TELEMETRY"] == "0"
    assert adapter.environment["CODEGRAPH_NO_UPDATE_CHECK"] == "1"
    status = adapter.ensure_index(project)
    assert status["initialized"] is True
    assert (project / ".codegraph" / "fake-index").is_file()


def test_code_doctor_setup_ready_and_version_attention(tmp_path: Path, monkeypatch) -> None:
    vault, repo_id = copy_vault(tmp_path)
    monkeypatch.delenv("MIRRORARC_CODEGRAPH", raising=False)
    monkeypatch.setenv("PATH", "")
    setup = doctor_report(vault, repo_id)
    assert setup["verdict"] == "Setup needed"
    assert "v1.5.0/install.sh" in setup["install_command"]

    binary = fake_codegraph(tmp_path)
    ready = doctor_report(vault, repo_id, binary=binary, verbose=True)
    assert ready["verdict"] == "Ready"
    assert ready["diagnostics"]["managed_environment"]["CODEGRAPH_TELEMETRY"] == "0"
    monkeypatch.setenv("FAKE_CODEGRAPH_VERSION", "1.4.0")
    attention = doctor_report(vault, repo_id, binary=binary)
    assert attention["verdict"] == "Attention"
    assert attention["provider_version"] == "1.4.0"


def test_analysis_context_catalog_staleness_and_failure_preserve_valid_result(tmp_path: Path, monkeypatch) -> None:
    vault, repo_id = copy_vault(tmp_path)
    binary = fake_codegraph(tmp_path)
    monkeypatch.setenv("MIRRORARC_CODEGRAPH", str(binary))
    result = analyze_repository(
        vault,
        repo_id,
        symbol="demand_change",
        changed_paths=["src/grid_evidence/summary.py"],
    )
    assert result["freshness_state"] == "local-uncommitted"
    assert result["files"][0]["hash"]
    assert result["files"][0]["line_ranges"]
    assert result["affected_tests"] == [
        {"path": "tests/test_summary.py", "basis": "symbol-impact", "confidence": "medium"}
    ]
    provider_caches = list((vault / CACHE_ROOT).rglob(".codegraph"))
    assert provider_caches
    assert all((vault / CACHE_ROOT).resolve() in item.resolve().parents for item in provider_caches)
    assert not (vault / "_fixtures" / "repos" / "pipeline" / ".codegraph").exists()

    dynamic = build_dynamic_code_context(vault, result)
    resolved = resolve_dynamic_context(vault, dynamic["definition"]["definition_id"])
    assert resolved["resolved_revision"] == result["resolved_revision"]
    assert resolved["body_content_included"] is False
    frozen = freeze_code_context(vault, result)
    document = json.loads((vault / frozen["output_path"]).read_text(encoding="utf-8"))
    assert document["offline_complete"] is True
    assert document["citations"][0]["revision"] == result["resolved_revision"]
    assert document["citations"][0]["file_hash"]
    assert document["omissions"] == []

    report, warnings, errors = build_report(vault)
    assert not errors
    code = report["code_intelligence"]["repositories"][0]
    assert code["analysis"]["files"][0]["excerpt_included"] is False
    assert "excerpt" not in code["analysis"]["files"][0]
    content_report = code_intelligence_catalog_report(vault, include_excerpts=True)
    content_file = content_report["repositories"][0]["analysis"]["files"][0]
    assert content_file["excerpt_included"] is True
    assert content_file["excerpt"]
    html = render_html(report, warnings, errors)
    assert 'id="code-view-tab"' in html
    assert "Add code evidence to context" in html
    assert "passive HTML cannot create one" in html

    source = vault / "_fixtures" / "repos" / "pipeline" / "src" / "grid_evidence" / "summary.py"
    source.write_text(source.read_text(encoding="utf-8") + "\n# controlled change\n", encoding="utf-8")
    stale = status_report(vault, repo_id)["items"][0]
    assert stale["freshness_state"] == "stale"
    assert ContextStore(vault).status(frozen["context_id"])["packs"][0]["freshness_state"] == "stale"

    monkeypatch.setenv("FAKE_CODEGRAPH_FAIL", "1")
    with pytest.raises(Exception, match="local analysis command failed"):
        analyze_repository(vault, repo_id, symbol="demand_change")
    failed = status_report(vault, repo_id)["items"][0]
    assert failed["freshness_state"] == "failed"
    assert failed["analysis"]["analysis_id"] == result["analysis_id"]


def test_code_cli_json_and_human_states(tmp_path: Path, monkeypatch, capsys) -> None:
    vault, repo_id = copy_vault(tmp_path)
    binary = fake_codegraph(tmp_path)
    monkeypatch.setenv("MIRRORARC_CODEGRAPH", str(binary))
    assert main(["--root", str(vault), "code", "doctor", "--repo", repo_id]) == 0
    assert capsys.readouterr().out.splitlines()[0] == "Ready"
    assert main([
        "--root", str(vault), "code", "analyze", "--repo", repo_id,
        "--symbol", "demand_change", "--changed-path", "src/grid_evidence/summary.py",
        "--context", "frozen", "--json",
    ]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["analysis_kind"] == "change"
    assert payload["context"]["mode"] == "frozen"
    assert main(["--root", str(vault), "code", "status", "--repo", repo_id, "--json"]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["summary"] == {"repositories": 1, "current": 1, "attention": 0}


def test_changed_local_tree_gets_a_distinct_analysis_identity(tmp_path: Path, monkeypatch) -> None:
    vault, repo_id = copy_vault(tmp_path)
    binary = fake_codegraph(tmp_path)
    monkeypatch.setenv("MIRRORARC_CODEGRAPH", str(binary))
    first = analyze_repository(vault, repo_id, symbol="demand_change")
    frozen = freeze_code_context(vault, first)
    source = vault / "_fixtures" / "repos" / "pipeline" / "src" / "grid_evidence" / "summary.py"
    source.write_text(source.read_text(encoding="utf-8") + "\n# a new synthetic tree\n", encoding="utf-8")
    second = analyze_repository(vault, repo_id, symbol="demand_change")
    assert second["local_tree_hash"] != first["local_tree_hash"]
    assert second["analysis_id"] != first["analysis_id"]
    assert (vault / CACHE_ROOT / repo_id / "analyses" / f"{first['analysis_id']}.json").is_file()
    assert (vault / CACHE_ROOT / repo_id / "analyses" / f"{second['analysis_id']}.json").is_file()
    frozen_status = ContextStore(vault).status(frozen["context_id"])["packs"][0]
    assert frozen_status["freshness_state"] == "stale"
    assert frozen_status["stale_reason"] == "newer repository evidence is available"
    repeated = analyze_repository(vault, repo_id, symbol="demand_change")
    assert repeated["analysis_id"] == second["analysis_id"]
    assert repeated["analysis_hash"] == second["analysis_hash"]
    assert repeated["created_at"] == second["created_at"]


def test_frozen_code_context_records_file_budget_omissions(tmp_path: Path, monkeypatch) -> None:
    vault, repo_id = copy_vault(tmp_path)
    binary = fake_codegraph(tmp_path)
    monkeypatch.setenv("MIRRORARC_CODEGRAPH", str(binary))
    profile_path = vault / "_meta" / "profile.yml"
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    profile["context_defaults"]["max_files"] = 1
    profile_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")

    analysis = analyze_repository(
        vault,
        repo_id,
        symbol="demand_change",
        changed_paths=["src/grid_evidence/summary.py"],
    )
    assert len(analysis["files"]) > 1
    frozen = freeze_code_context(vault, analysis)
    assert frozen["included_count"] == 1
    assert any(item["reason"] == "file_budget" for item in frozen["omissions"])


@pytest.mark.skipif(not os.environ.get("MIRRORARC_CODEGRAPH_SMOKE"), reason="set MIRRORARC_CODEGRAPH_SMOKE to the v1.5.0 executable")
def test_real_codegraph_v1_5_0_smoke(tmp_path: Path, monkeypatch) -> None:
    vault, repo_id = copy_vault(tmp_path)
    binary = Path(os.environ["MIRRORARC_CODEGRAPH_SMOKE"])
    monkeypatch.setenv("MIRRORARC_CODEGRAPH", str(binary))
    result = analyze_repository(
        vault,
        repo_id,
        symbol="demand_change",
        changed_paths=["src/grid_evidence/summary.py"],
    )
    assert result["provider_version"] == "1.5.0"
    assert result["symbols"][0]["path"] == "src/grid_evidence/summary.py"
    assert result["symbols"][0]["start_line"] == 8
    assert any(item["path"] == "tests/test_summary.py" for item in result["affected_tests"])
