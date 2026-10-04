# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from mirrorarc.changes import journal, worker
from mirrorarc.knowledge_views.lifecycle import promote_view, review_view
from mirrorarc.knowledge_views.render import render_lens
from mirrorarc.knowledge_views.store import KnowledgeViewError, KnowledgeViewStore
from mirrorarc.relationships.deterministic import refresh


REPO_ROOT = Path(__file__).resolve().parents[1]


class FixtureConverter:
    class Result:
        text_content = "Synthetic source evidence for deterministic L2 rendering."

    def convert(self, _path: str) -> "FixtureConverter.Result":
        return self.Result()


def copy_template(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    shutil.copytree(REPO_ROOT / "template", vault)
    return vault


def add_native_source(vault: Path, name: str, body: str) -> None:
    (vault / "20_sources" / name).write_text(
        "---\n"
        f"title: {name}\n"
        "type: authoritative-record\nstatus: active\ndomain: sources\n"
        "created: '2026-07-21'\nupdated: '2026-07-21'\n"
        "markdown_category: authoritative_markdown_source\nauthority: authoritative\n"
        "---\n\n" + body + "\n",
        encoding="utf-8",
    )


def materialize_source(vault: Path, content: bytes, *, event_kind: str = "created", source_id: str = "") -> tuple[Path, dict]:
    source = vault / "20_sources" / "opaque.docx"
    source.write_bytes(content)
    journal.record_event(
        vault,event_kind,current_path="20_sources/opaque.docx",source_id=source_id,
    )
    result = worker.process_next_event(
        vault,"view-worker",materialize_kwargs={
            "converter":FixtureConverter(),"converter_name":"fixture","converter_version":"1",
            "append_audit":False,
        },
    )
    assert result["finish_status"] == "applied"
    return source,result["materialization"]["record"]


def test_one_deterministic_view_synthesizes_many_sources_with_citations_and_is_idempotent(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)
    for index in range(5):
        add_native_source(vault,f"source-{index}.md",f"Synthetic evidence item {index}.")
    refresh(vault)

    first = render_lens(vault,"orientation")
    path = vault / first["output_path"]
    first_bytes = path.read_bytes()
    first_mtime = path.stat().st_mtime_ns
    second = render_lens(vault,"orientation")

    assert first["state"] == "generated"
    assert len(first["citations"]) == 5
    assert first["view_id"] == second["view_id"]
    assert second["unchanged"] is True
    assert path.read_bytes() == first_bytes
    assert path.stat().st_mtime_ns == first_mtime
    assert "## Evidence" in first_bytes.decode()
    assert first_bytes.decode().count("- Source: `20_sources/source-") == 5
    status = KnowledgeViewStore(vault).status()
    assert status["total"] == 1
    assert status["dependencies"] == 5
    assert status["persistent"] < 5


def test_reviewed_view_is_preserved_stale_and_replaced_by_distinct_candidate(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)
    source, record = materialize_source(vault,b"synthetic version one")
    generated = render_lens(vault,"orientation")
    reviewed = review_view(vault,generated["view_id"],reviewer="fixture-reviewer")
    reviewed_path = vault / reviewed["output_path"]
    reviewed_bytes = reviewed_path.read_bytes()
    source.write_bytes(b"synthetic version two")
    journal.record_event(
        vault,"modified",current_path="20_sources/opaque.docx",source_id=record["source_id"],
    )
    changed = worker.process_next_event(
        vault,"view-worker",materialize_kwargs={
            "converter":FixtureConverter(),"converter_name":"fixture","converter_version":"1",
            "append_audit":False,
        },
    )

    stale = KnowledgeViewStore(vault).get(generated["view_id"])
    candidate = render_lens(vault,"orientation")

    assert changed["finish_status"] == "applied"
    assert stale is not None and stale["state"] == "stale"
    assert reviewed_path.read_bytes() == reviewed_bytes
    assert candidate["view_id"] != generated["view_id"]
    assert candidate["state"] == "generated"
    assert KnowledgeViewStore(vault).status()["by_state"] == {"generated":1,"stale":1}


def test_reviewed_view_becomes_stale_when_lens_definition_changes(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)
    add_native_source(vault, "source.md", "Synthetic evidence for definition invalidation.")
    refresh(vault)
    generated = render_lens(vault, "orientation")
    reviewed = review_view(vault, generated["view_id"], reviewer="fixture-reviewer")
    reviewed_path = vault / reviewed["output_path"]
    reviewed_bytes = reviewed_path.read_bytes()

    profile_path = vault / "_meta" / "profile.yml"
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    profile["knowledge_lenses"]["orientation"]["purpose"] += " Updated purpose."
    profile_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")
    candidate = render_lens(vault, "orientation")
    stale = KnowledgeViewStore(vault).get(generated["view_id"])

    assert candidate["view_id"] != generated["view_id"]
    assert stale is not None and stale["state"] == "stale"
    assert stale["refresh_queued"] == 1
    assert "definition" in stale["stale_reason"]
    assert reviewed_path.read_bytes() == reviewed_bytes


def test_promotion_requires_explicit_review_and_preserves_derivation(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)
    add_native_source(vault,"source.md","Synthetic evidence for promotion.")
    refresh(vault)
    generated = render_lens(vault,"orientation")

    with pytest.raises(KnowledgeViewError,match="reviewed"):
        promote_view(
            vault,generated["view_id"],target=Path("70_outputs/promoted.md"),
            reviewer="fixture-reviewer",reason="Explicit promotion fixture.",
        )
    review_view(vault,generated["view_id"],reviewer="fixture-reviewer")
    promoted = promote_view(
        vault,generated["view_id"],target=Path("70_outputs/promoted.md"),
        reviewer="fixture-reviewer",reason="Explicit promotion fixture.",
    )

    target = vault / promoted["target"]
    frontmatter = yaml.safe_load(target.read_text(encoding="utf-8").split("---",2)[1])
    assert frontmatter["markdown_category"] == "authoritative_markdown_source"
    assert frontmatter["promotion_provenance"]["source_view_id"] == generated["view_id"]
    assert frontmatter["promotion_provenance"]["reviewer"] == "fixture-reviewer"
    with pytest.raises(KnowledgeViewError,match="already exists"):
        promote_view(
            vault,generated["view_id"],target=Path("70_outputs/promoted.md"),
            reviewer="fixture-reviewer",reason="Duplicate blocked.",
        )


def test_builtin_profiles_do_not_create_one_lens_per_source_defaults() -> None:
    for path in sorted((REPO_ROOT / "src" / "mirrorarc" / "builtin_profiles").glob("*.yml")):
        profile = yaml.safe_load(path.read_text(encoding="utf-8"))
        lenses = profile.get("knowledge_lenses",{})
        assert 1 <= len(lenses) <= 4
        assert all(lens.get("persistence") != "reviewed" for lens in lenses.values())
        assert profile.get("review_policy",{}).get("automatic_promotion") is False
