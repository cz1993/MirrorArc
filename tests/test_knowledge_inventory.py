# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

import json
import shutil
from pathlib import Path

import yaml

from mirrorarc import lint
from mirrorarc.knowledge_inventory import build_inventory, stable_projection_id
from mirrorarc.mirrors import office


REPO_ROOT = Path(__file__).resolve().parents[1]


class FixtureConverter:
    class Result:
        text_content = "Synthetic fixture evidence."

    def convert(self, _path: str) -> "FixtureConverter.Result":
        return self.Result()


def copy_template(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    shutil.copytree(REPO_ROOT / "template", vault)
    return vault


def test_office_projection_identity_is_stable_and_second_sync_creates_no_markdown(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)
    source = vault / "20_sources" / "evidence.docx"
    source.write_bytes(b"synthetic fixture bytes")
    manifest = office.empty_manifest()
    config = office.load_mirror_config(vault)

    first = office.sync_one(
        source, vault, FixtureConverter(), False, False, config, {}, manifest, "fixture", "1"
    )
    office.write_source_manifest(vault, manifest)
    markdown_after_first = sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*.md"))
    first_record = dict(manifest["records"][0])

    second = office.sync_one(
        source, vault, FixtureConverter(), False, False, config, {}, manifest, "fixture", "1"
    )
    office.write_source_manifest(vault, manifest)
    markdown_after_second = sorted(path.relative_to(vault).as_posix() for path in vault.rglob("*.md"))
    report = build_inventory(vault)

    assert first == "created"
    assert second == "unchanged"
    assert markdown_after_second == markdown_after_first
    assert manifest["records"][0]["source_id"] == first_record["source_id"]
    assert manifest["records"][0]["projection_id"] == first_record["projection_id"]
    assert first_record["projection_id"] == stable_projection_id(first_record["source_id"])
    assert report["summary"]["opaque_sources_requiring_l1"] == 1
    assert report["summary"]["active_l1_projections"] == 1
    assert report["errors"] == []


def test_native_markdown_is_registered_directly_without_a_sibling(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)
    source = vault / "20_sources" / "native.md"
    source.write_text(
        "---\n"
        "title: Native source\n"
        "type: authoritative-record\n"
        "status: active\n"
        "domain: sources\n"
        "created: '2026-07-21'\n"
        "updated: '2026-07-21'\n"
        "markdown_category: authoritative_markdown_source\n"
        "authority: authoritative\n"
        "---\n\n# Native source\n",
        encoding="utf-8",
    )

    report = build_inventory(vault)

    assert report["native_source_mode"] == "direct"
    assert report["summary"]["native_readable_sources"] == 1
    assert report["summary"]["native_sources_requiring_projection"] == 0
    assert not (source.parent / "native.mirror.md").exists()


def test_duplicate_projection_identity_and_orphan_l1_are_reported(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)
    for name in ("a.docx", "b.docx"):
        (vault / "20_sources" / name).write_bytes(f"synthetic {name}".encode())
    orphan = vault / "_mirrors" / "20_sources" / "orphan.md"
    orphan.parent.mkdir(parents=True)
    orphan.write_text(
        "---\ntitle: Orphan\ntype: source-mirror\nstatus: active\ndomain: sources\n"
        "created: '2026-07-21'\nupdated: '2026-07-21'\n---\n\n"
        "%% AUTO-GENERATED BELOW — DO NOT EDIT %%\n",
        encoding="utf-8",
    )
    manifest = {
        "schema_version": 1,
        "records": [
            {
                "source_id": "src_a",
                "projection_id": "l1_duplicate",
                "current_source_path": "20_sources/a.docx",
                "mirror_path": "_mirrors/20_sources/a.md",
                "lifecycle_state": "clean",
            },
            {
                "source_id": "src_b",
                "projection_id": "l1_duplicate",
                "current_source_path": "20_sources/b.docx",
                "mirror_path": "_mirrors/20_sources/b.md",
                "lifecycle_state": "clean",
            },
        ],
    }
    (vault / "_meta" / "source-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    report = build_inventory(vault)

    assert any("projection identity is claimed by 2" in item for item in report["errors"])
    assert any("orphan L1 projection" in item for item in report["errors"])


def test_unclassified_generated_markdown_fails_lint(tmp_path: Path, capsys) -> None:
    vault = copy_template(tmp_path)
    unclassified = vault / "20_sources" / "generated-summary.md"
    unclassified.write_text(
        "---\ntitle: Generated summary\ntype: mystery\nstatus: active\ndomain: sources\n"
        "created: '2026-07-21'\nupdated: '2026-07-21'\n---\n\nSynthetic generated summary.\n",
        encoding="utf-8",
    )

    result = lint.main(vault)
    output = capsys.readouterr().out

    assert result == 1
    assert "Unexplained user-facing Markdown: 1" in output
    assert "20_sources/generated-summary.md" in output


def test_native_source_policy_rejects_unknown_mode(tmp_path: Path) -> None:
    vault = copy_template(tmp_path)
    profile_path = vault / "_meta" / "profile.yml"
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    profile["policy_defaults"]["native_source_mode"] = "duplicate_everything"
    profile_path.write_text(yaml.safe_dump(profile, sort_keys=False), encoding="utf-8")

    assert lint.main(vault) == 1
