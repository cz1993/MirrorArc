# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

import vaultwright.navigation as navigation
from vaultwright.navigation import (
    MAX_NAVIGATION_CONFIG_BYTES,
    MAX_NOTE_BYTES,
    NavigationAccessError,
    NavigationStaleError,
    build_navigation_model,
    read_document,
)


def write_profile(vault: Path, content_root: str = "25_research") -> None:
    meta = vault / "_meta"
    meta.mkdir(parents=True, exist_ok=True)
    profile = {
        "schema_version": 1,
        "id": "navigation-test",
        "name": "Navigation Test",
        "profile_version": "1.0.0",
        "domains": {
            "research": {
                "folder": content_root,
                "purpose": "Synthetic navigation test notes.",
            }
        },
        "note_types": {"note": {"purpose": "A synthetic note."}},
        "statuses": {"active": {"purpose": "Current synthetic note."}},
        "required_properties": ["title", "type", "status", "domain", "created", "updated"],
        "optional_properties": ["owner", "related"],
        "folder_plan": [{"path": content_root, "domain": "research"}],
        "templates": [],
        "views": [],
        "skills": [],
        "benchmark_tasks": [],
        "policy_defaults": {
            "mirror_mode": "dedicated",
            "mirror_root": "_generated",
            "mirror_status": "active",
            "repo_stub_status": "active",
            "repo_notes_dir": f"{content_root}/repos",
            "original_sources_authoritative": True,
            "real_data_in_repo": False,
        },
    }
    (meta / "profile.yml").write_text(
        yaml.safe_dump(profile, sort_keys=False),
        encoding="utf-8",
    )
    (meta / "mirror-config.yml").write_text(
        "office_mirrors:\n  mode: dedicated\n  root: _generated\n",
        encoding="utf-8",
    )


def write_note(vault: Path, rel: str, text: str) -> Path:
    path = vault / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def by_path(model: dict[str, object]) -> dict[str, dict[str, object]]:
    return {node["path"]: node for node in model["nodes"]}  # type: ignore[index]


def test_scans_profile_neutral_roots_and_minimizes_metadata(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    write_profile(vault)
    (vault / "tools").mkdir()
    (vault / "tools" / "repos.yml").write_text(
        "settings:\n  notes_dir: 90_repo_mirrors\nrepos: []\n",
        encoding="utf-8",
    )
    write_note(vault, "INDEX.md", "# Start here\n")
    write_note(
        vault,
        "25_research/concept.md",
        "---\n"
        "title: Concept\n"
        "type: note\n"
        "status: active\n"
        "domain: research\n"
        "updated: 2026-07-12\n"
        "private_customer_id: must-not-leak\n"
        "nested_secret:\n  token: must-not-leak\n"
        "---\n"
        "# Concept body\n"
        "Unique body sentence must not enter the model.\n",
    )
    write_note(vault, "_generated/25_research/source.md", "# Office mirror\n")
    write_note(vault, "90_repo_mirrors/repository.md", "# Repository mirror\n")
    write_note(vault, "30_customers/legacy.md", "# Wrong profile root\n")
    write_note(vault, "README.md", "# Repository readme, not a vault note\n")
    write_note(vault, "_meta/private.md", "# Private control material\n")

    model, warnings, errors = build_navigation_model(vault)

    nodes = by_path(model)
    assert list(nodes) == [
        "25_research/concept.md",
        "90_repo_mirrors/repository.md",
        "_generated/25_research/source.md",
        "INDEX.md",
    ]
    concept = nodes["25_research/concept.md"]
    assert concept["frontmatter"] == {
        "domain": "research",
        "status": "active",
        "title": "Concept",
        "type": "note",
        "updated": "2026-07-12",
    }
    assert "content" not in concept
    assert "Unique body sentence" not in repr(model)
    assert warnings == []
    assert errors == []


def test_private_frontmatter_does_not_leak_through_link_warnings(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    write_profile(vault, "notes")
    write_note(
        vault,
        "notes/Public.md",
        "---\n"
        "title: Public\n"
        'private_case: "[[Patient John Doe HIV]]"\n'
        "---\n"
        "# Public body\n",
    )

    model, warnings, errors = build_navigation_model(vault)

    assert "Patient John Doe HIV" not in repr(model)
    assert warnings == []
    assert errors == []


def test_invalid_yaml_timestamp_warns_without_aborting_scan(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    write_profile(vault, "notes")
    write_note(
        vault,
        "notes/Invalid Date.md",
        "---\ntitle: Invalid date\nupdated: 2026-99-99\n---\n# Still readable\n",
    )

    model, warnings, errors = build_navigation_model(vault)

    assert by_path(model)["notes/Invalid Date.md"]["title"] == "Still readable"
    assert warnings == [
        "notes/Invalid Date.md: invalid YAML frontmatter (ValueError)"
    ]
    assert errors == []


def test_headings_links_and_backlinks_are_one_hop_and_deterministic(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    write_profile(vault, "notes")
    write_note(
        vault,
        "notes/Start.md",
        "---\nrelated: ['[[Middle]]']\n---\n"
        "# Start\n"
        "## Read *this* first!\n"
        "## Read this first!\n"
        "Setext heading\n"
        "---------------\n"
        "[[#Start]]\n"
        "[Finish](<Finish.md#result>)\n"
        "`[[Ignored]]`\n"
        "```md\n[[Also Ignored]]\n```\n",
    )
    write_note(vault, "notes/Middle.md", "# Middle\nSee [[Finish]].\n")
    write_note(vault, "notes/Finish.md", "# Finish\n## Result\n")

    first = build_navigation_model(vault)
    second = build_navigation_model(vault)

    assert first == second
    model, warnings, errors = first
    nodes = by_path(model)
    assert nodes["notes/Start.md"]["headings"] == [
        {"level": 1, "text": "Start", "anchor": "start"},
        {"level": 2, "text": "Read this first!", "anchor": "read-this-first"},
        {"level": 2, "text": "Read this first!", "anchor": "read-this-first-1"},
        {"level": 2, "text": "Setext heading", "anchor": "setext-heading"},
    ]
    assert nodes["notes/Start.md"]["outbound"] == [
        "notes/Finish.md",
        "notes/Middle.md",
        "notes/Start.md",
    ]
    assert nodes["notes/Finish.md"]["inbound"] == ["notes/Middle.md", "notes/Start.md"]
    assert nodes["notes/Middle.md"]["inbound"] == ["notes/Start.md"]
    assert model["edges"] == [
        {"source": "notes/Middle.md", "target": "notes/Finish.md", "kinds": ["wikilink"]},
        {"source": "notes/Start.md", "target": "notes/Finish.md", "kinds": ["markdown"]},
        {"source": "notes/Start.md", "target": "notes/Middle.md", "kinds": ["wikilink"]},
        {"source": "notes/Start.md", "target": "notes/Start.md", "kinds": ["wikilink"]},
    ]
    assert warnings == []
    assert errors == []


def test_ambiguous_unresolved_and_unsafe_links_warn_without_guessing(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    write_profile(vault, "notes")
    write_note(
        vault,
        "notes/Start.md",
        "# Start\n"
        "[[Shared]]\n"
        "[[Missing]]\n"
        "[[Documents.base]]\n"
        "[[_meta/conventions]]\n"
        "[[_meta/domain-map]]\n"
        "[[_meta/../../outside]]\n"
        "[malformed](http://[)\n"
        "[escape](../../../outside.md)\n",
    )
    write_note(vault, "notes/alpha/Shared.md", "# Alpha shared\n")
    write_note(vault, "notes/beta/Shared.md", "# Beta shared\n")

    model, warnings, errors = build_navigation_model(vault)

    assert by_path(model)["notes/Start.md"]["outbound"] == []
    assert warnings == [
        "notes/Start.md: ambiguous wikilink target Shared: notes/alpha/Shared.md, notes/beta/Shared.md",
        "notes/Start.md: unresolved wikilink target: Missing",
        "notes/Start.md: unsafe markdown target ignored: ../../../outside.md",
        "notes/Start.md: unsafe markdown target ignored: http://[",
        "notes/Start.md: unsafe wikilink target ignored: _meta/../../outside",
    ]
    assert errors == []


def test_authored_trails_preserve_order_and_reject_bad_paths(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    write_profile(vault, "notes")
    write_note(vault, "notes/First.md", "# First\n")
    write_note(vault, "notes/Second.md", "# Second\n")
    write_note(vault, "notes/alpha/Shared.md", "# Alpha shared\n")
    write_note(vault, "notes/beta/Shared.md", "# Beta shared\n")
    (vault / "_meta" / "navigation.yml").write_text(
        "schema_version: 1\n"
        "trails:\n"
        "  - id: learn-core\n"
        "    title: Learn the core\n"
        "    goal: Understand the decision in context.\n"
        "    audience: [newcomers, reviewers]\n"
        "    steps:\n"
        "      - path: notes/Second.md\n"
        "        why: See the result before the rationale.\n"
        "      - path: notes/First.md\n"
        "        why: Then read the rationale.\n"
        "  - id: ambiguous\n"
        "    title: Ambiguous\n"
        "    goal: Must be rejected.\n"
        "    audience: reviewers\n"
        "    steps:\n"
        "      - path: Shared.md\n"
        "        why: This basename is not unique.\n"
        "  - id: missing\n"
        "    title: Missing\n"
        "    goal: Must be rejected.\n"
        "    audience: reviewers\n"
        "    steps:\n"
        "      - path: notes/Nope.md\n"
        "        why: This note does not exist.\n"
        "  - id: unsafe\n"
        "    title: Unsafe\n"
        "    goal: Must be rejected.\n"
        "    audience: reviewers\n"
        "    steps:\n"
        "      - path: ../outside.md\n"
        "        why: This leaves the vault.\n",
        encoding="utf-8",
    )

    model, warnings, errors = build_navigation_model(vault)

    assert model["trails"] == [
        {
            "id": "learn-core",
            "title": "Learn the core",
            "goal": "Understand the decision in context.",
            "audience": ["newcomers", "reviewers"],
            "steps": [
                {
                    "path": "notes/Second.md",
                    "node_id": "notes/Second.md",
                    "why": "See the result before the rationale.",
                },
                {
                    "path": "notes/First.md",
                    "node_id": "notes/First.md",
                    "why": "Then read the rationale.",
                },
            ],
        }
    ]
    assert warnings == []
    assert any("path is ambiguous: Shared.md" in error for error in errors)
    assert any("path is missing: notes/Nope.md" in error for error in errors)
    assert any("path is unsafe: ../outside.md" in error for error in errors)


def test_authored_trail_exact_root_path_beats_nested_basename(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    write_profile(vault, "notes")
    write_note(vault, "INDEX.md", "# Root index\n")
    write_note(vault, "notes/INDEX.md", "# Nested index\n")
    (vault / "_meta" / "navigation.yml").write_text(
        "schema_version: 1\n"
        "trails:\n"
        "  - id: root-start\n"
        "    title: Root start\n"
        "    goal: Start at the root landmark.\n"
        "    audience: newcomers\n"
        "    steps:\n"
        "      - path: INDEX.md\n"
        "        why: Use the explicit root entry point.\n",
        encoding="utf-8",
    )

    model, warnings, errors = build_navigation_model(vault)

    assert model["trails"][0]["steps"][0]["path"] == "INDEX.md"
    assert warnings == []
    assert errors == []


def test_navigation_config_requires_schema_version_one(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    write_profile(vault, "notes")
    write_note(vault, "notes/First.md", "# First\n")
    (vault / "_meta" / "navigation.yml").write_text(
        "schema_version: 2\n"
        "trails:\n"
        "  - id: must-not-load\n"
        "    title: Must not load\n"
        "    goal: Prove unsupported schemas are rejected.\n"
        "    audience: reviewers\n"
        "    steps:\n"
        "      - path: notes/First.md\n"
        "        why: A valid-looking trail must not bypass the version gate.\n",
        encoding="utf-8",
    )

    model, warnings, errors = build_navigation_model(vault)

    assert model["trails"] == []
    assert warnings == []
    assert errors == ["_meta/navigation.yml: schema_version must be 1"]


def test_navigation_rejects_oversized_notes_and_config(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    write_profile(vault, "notes")
    oversized = write_note(vault, "notes/Oversized.md", "# Oversized\n")
    with oversized.open("r+b") as handle:
        handle.truncate(MAX_NOTE_BYTES + 1)
    navigation = vault / "_meta" / "navigation.yml"
    navigation.write_text("schema_version: 1\ntrails: []\n", encoding="utf-8")
    with navigation.open("r+b") as handle:
        handle.truncate(MAX_NAVIGATION_CONFIG_BYTES + 1)

    model, warnings, errors = build_navigation_model(vault)

    assert model["nodes"] == []
    assert warnings == []
    assert "notes/Oversized.md: exceeds the 16 MiB Navigator note limit" in errors
    assert "_meta/navigation.yml: exceeds the 1 MiB navigation-config limit" in errors


def test_read_document_rechecks_note_size_after_model_build(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    write_profile(vault, "notes")
    note = write_note(vault, "notes/Grows.md", "# Initially small\n")
    model, _, errors = build_navigation_model(vault)
    assert errors == []

    with note.open("r+b") as handle:
        handle.truncate(MAX_NOTE_BYTES + 1)

    with pytest.raises(NavigationAccessError, match="16 MiB Navigator note limit"):
        read_document(vault, "notes/Grows.md", model)


def test_read_document_rejects_a_note_changed_after_model_build(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    write_profile(vault, "notes")
    note = write_note(
        vault,
        "notes/Changes.md",
        "---\ntitle: Current\nstatus: active\n---\n# Original body\n",
    )
    model, _, errors = build_navigation_model(vault)
    assert errors == []

    note.write_text(
        "---\ntitle: Changed\nstatus: archived\n---\n# Revised body\n",
        encoding="utf-8",
    )

    with pytest.raises(NavigationStaleError, match="rescan required"):
        read_document(vault, "notes/Changes.md", model)


def test_read_document_requires_a_current_safe_model_path(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    write_profile(vault, "notes")
    note = write_note(
        vault,
        "notes/Read.md",
        "---\ntitle: Read safely\nsecret: omitted\n---\n# Body\nMarkdown source.\n",
    )
    write_note(vault, "_meta/private.md", "# Must not be read\n")
    model, _, _ = build_navigation_model(vault)

    document = read_document(vault, "notes/Read.md", model)
    assert document["title"] == "Read safely"
    assert document["frontmatter"] == {"title": "Read safely"}
    assert document["content"] == note.read_text(encoding="utf-8")
    assert document["content_type"] == "text/markdown"

    for unsafe in ("../outside.md", "/etc/passwd", "_meta/private.md", "tools/config.md"):
        with pytest.raises(NavigationAccessError):
            read_document(vault, unsafe, model)

    spoofed = {"nodes": [{"path": "_meta/private.md"}]}
    with pytest.raises(NavigationAccessError):
        read_document(vault, "_meta/private.md", spoofed)


def test_reserved_roots_are_case_insensitive_across_platforms(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    write_profile(vault, "_META")
    write_note(vault, "_META/private.md", "# Private control material\nsecret marker\n")

    model, warnings, errors = build_navigation_model(vault)

    assert model["nodes"] == []
    assert warnings == []
    assert errors == []
    spoofed = {"nodes": [{"path": "_META/private.md"}]}
    with pytest.raises(NavigationAccessError):
        read_document(vault, "_META/private.md", spoofed)


def test_private_secret_and_runtime_directories_are_never_scanned(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    write_profile(vault, "notes")
    write_note(vault, "notes/Public.md", "# Public\n")
    write_note(vault, "notes/PRIVATE/person.md", "# Private person\n")
    write_note(vault, "notes/Secrets/token.md", "# Secret token\n")
    write_note(vault, "notes/.vaultwright/runtime.md", "# Runtime material\n")

    model, warnings, errors = build_navigation_model(vault)

    assert list(by_path(model)) == ["notes/Public.md"]
    assert warnings == []
    assert errors == []


def test_candidate_and_link_intermediates_stop_at_resource_caps(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    write_profile(vault, "notes")
    for name in ("A.md", "B.md", "C.md"):
        write_note(vault, f"notes/{name}", "# Note\n")
    monkeypatch.setattr(navigation, "MAX_NAVIGATION_DOCUMENTS", 2)

    model, warnings, errors = build_navigation_model(vault)

    assert len(model["nodes"]) == 2
    assert warnings == []
    assert errors == ["navigation document limit exceeded (2); narrow the profile roots"]

    monkeypatch.setattr(navigation, "MAX_NAVIGATION_DOCUMENTS", 5_000)
    monkeypatch.setattr(navigation, "MAX_LINKS_PER_DOCUMENT", 2)
    link_vault = tmp_path / "link-vault"
    link_vault.mkdir()
    write_profile(link_vault, "notes")
    write_note(link_vault, "notes/Links.md", "# Links\n[[Missing]] [[Missing]] [[Missing]]\n")

    _model, warnings, errors = build_navigation_model(link_vault)

    assert warnings == ["notes/Links.md: unresolved wikilink target: Missing"]
    assert errors == ["notes/Links.md: exceeds the 2-link Navigator note limit"]


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_symlinks_are_not_scanned_and_a_post_scan_symlink_swap_is_rejected(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    write_profile(vault, "notes")
    outside = write_note(tmp_path, "outside.md", "# Outside\nPrivate source.\n")
    linked = vault / "notes" / "Linked.md"
    linked.parent.mkdir(parents=True, exist_ok=True)
    linked.symlink_to(outside)
    regular = write_note(vault, "notes/Regular.md", "# Regular\n")

    model, _, _ = build_navigation_model(vault)

    assert "notes/Linked.md" not in by_path(model)
    regular.unlink()
    regular.symlink_to(outside)
    with pytest.raises(NavigationAccessError, match="missing, linked, or outside"):
        read_document(vault, "notes/Regular.md", model)
