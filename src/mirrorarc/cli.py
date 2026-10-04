# SPDX-License-Identifier: AGPL-3.0-or-later
"""Installable MirrorArc console entry point.

The packaged command owns profile commands and migrated runtime behavior directly. Vault-local
operator scripts remain compatibility shims for users who run commands from inside a copied vault.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import shlex
import shutil
import sys
import time
from pathlib import Path

from mirrorarc import __version__
from mirrorarc import benchmark as benchmark_module
from mirrorarc import catalog as catalog_module
from mirrorarc import conversion as conversion_module
from mirrorarc import doctor as doctor_module
from mirrorarc import lint as lint_module
from mirrorarc import knowledge_inventory as knowledge_inventory_module
from mirrorarc import m365 as m365_module
from mirrorarc import migration as migration_module
from mirrorarc import overlap as overlap_module
from mirrorarc import pilot as pilot_module
from mirrorarc import recovery as recovery_module
from mirrorarc import review_ledger as review_ledger_module
from mirrorarc import sandbox as sandbox_module
from mirrorarc.code_intelligence.adapter import CodeGraphError
from mirrorarc.code_intelligence.context import build_dynamic_code_context, freeze_code_context
from mirrorarc.code_intelligence.service import (
    CodeIntelligenceError,
    analyze_repository,
    doctor_report as code_doctor_report,
    status_report as code_status_report,
)
from mirrorarc.annotation_migration import (
    annotation_migration_plan,
    public_plan,
    write_annotation_sidecars,
)
from mirrorarc.changes import changed_sync as changed_sync_module
from mirrorarc.changes import feed as feed_module
from mirrorarc.changes import journal as journal_module
from mirrorarc.changes import native_watch as native_watch_module
from mirrorarc.changes import reconcile as reconcile_module
from mirrorarc.changes import replay as replay_module
from mirrorarc.changes import watch as watch_module
from mirrorarc.mirrors import github_repos as repo_sync_module
from mirrorarc.mirrors import office as office_sync_module
from mirrorarc.relationships.deterministic import refresh as refresh_relationships
from mirrorarc.relationships.proposals import propose as propose_relationship
from mirrorarc.relationships.store import RelationshipStore
from mirrorarc.relationships.model import RelationshipValidationError
from mirrorarc.knowledge_views.definitions import LensDefinitionError, load_lenses
from mirrorarc.knowledge_views.lifecycle import pin_view, promote_view, review_view
from mirrorarc.knowledge_views.render import render_lens
from mirrorarc.knowledge_views.store import KnowledgeViewError, KnowledgeViewStore
from mirrorarc.context_assembly.builder import (
    ContextAssemblyError,
    build_context,
    freeze_context,
    resolve_dynamic_context,
)
from mirrorarc.context_assembly.store import ContextStore, ContextStoreError
from mirrorarc.profile_migration import profile_migration_plan, write_profile_migration
from mirrorarc.profile_scaffold import DEFAULT_TEMPLATE_PROFILE_ID, scaffold_profile_vault
from mirrorarc.profiles import ProfileContract, ProfileValidationError, load_profile
from mirrorarc.views import profile_views_plan, write_profile_views

BUILTIN_PROFILE_DIR = Path(__file__).resolve().parent / "builtin_profiles"


def experimental_help(text: str) -> str:
    return f"[experimental] {text}"


def template_source() -> Path | None:
    env_root = os.environ.get("MIRRORARC_REPO") or os.environ.get("VAULTWRIGHT_REPO")
    candidates = []
    if env_root:
        candidates.append(Path(env_root))
    here = Path(__file__).resolve()
    candidates.extend(here.parents)
    for candidate in candidates:
        template = candidate / "template"
        if (template / "CLAUDE.md").exists():
            return template
    return None


def built_in_profile_paths() -> list[Path]:
    paths: list[Path] = []
    template = template_source()
    if template:
        paths.append(template / "_meta" / "profile.yml")
    if BUILTIN_PROFILE_DIR.exists():
        paths.extend(sorted(BUILTIN_PROFILE_DIR.glob("*.yml")))
    return paths


def built_in_profiles() -> dict[str, tuple[ProfileContract, Path]]:
    profiles: dict[str, tuple[ProfileContract, Path]] = {}
    for path in built_in_profile_paths():
        if not path.exists():
            continue
        profile = load_profile(path)
        if profile.id in profiles:
            previous_path = profiles[profile.id][1]
            raise ProfileValidationError(
                f"duplicate built-in profile id {profile.id}: {previous_path} and {path}"
            )
        profiles[profile.id] = (profile, path)
    return dict(sorted(profiles.items()))


def ensure_empty_or_missing(target: Path) -> None:
    if target.exists() and any(target.iterdir()):
        raise ValueError(f"refusing: '{target}' exists and is not empty")


def built_in_profile() -> tuple[ProfileContract, Path] | None:
    profiles = built_in_profiles()
    return profiles.get(DEFAULT_TEMPLATE_PROFILE_ID)


def print_profile_summary(profile: ProfileContract) -> None:
    summary = profile.summary()
    print(f"id: {summary['id']}")
    print(f"name: {summary['name']}")
    print(f"profile_version: {summary['profile_version']}")
    print(f"schema_version: {summary['schema_version']}")
    print(f"domains: {summary['domains']}")
    print(f"note_types: {summary['note_types']}")
    print(f"statuses: {summary['statuses']}")
    print(f"templates: {summary['templates']}")
    print(f"views: {summary['views']}")


def command_profile_list(args: argparse.Namespace) -> int:
    try:
        profiles = built_in_profiles()
    except ProfileValidationError as exc:
        print(f"profile list: invalid built-in profile: {exc}", file=sys.stderr)
        return 1
    if not profiles:
        print("profile list: no built-in profiles found", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps([profile.summary() for profile, _path in profiles.values()], indent=2, sort_keys=True))
    else:
        print("id\tversion\tname")
        for profile, _path in profiles.values():
            print(f"{profile.id}\t{profile.profile_version}\t{profile.name}")
    return 0


def load_current_profile(root: Path) -> tuple[ProfileContract, Path]:
    path = root / "_meta" / "profile.yml"
    if not path.exists():
        raise ProfileValidationError(f"missing profile: {path}")
    return load_profile(path), path


def load_optional_current_profile(root: Path) -> tuple[ProfileContract | None, Path]:
    path = root / "_meta" / "profile.yml"
    if not path.exists():
        return None, path
    return load_profile(path), path


def command_profile_show(args: argparse.Namespace) -> int:
    try:
        if args.profile_id:
            profiles = built_in_profiles()
            if not profiles:
                print("profile show: no built-in profiles found", file=sys.stderr)
                return 1
            loaded = profiles.get(args.profile_id)
            if not loaded:
                print(f"profile show: unknown built-in profile: {args.profile_id}", file=sys.stderr)
                return 1
            profile, path = loaded
        else:
            profile, path = load_current_profile(args.root.expanduser().resolve())
    except ProfileValidationError as exc:
        print(f"profile show: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(profile.as_dict(), indent=2, sort_keys=True))
    else:
        print_profile_summary(profile)
        print(f"path: {path}")
    return 0


def command_profile_validate(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    path = args.path.expanduser().resolve() if args.path else root / "_meta" / "profile.yml"
    try:
        profile = load_profile(path)
    except ProfileValidationError as exc:
        print(f"profile validate: {exc}", file=sys.stderr)
        return 1
    if args.json:
        payload = {"ok": True, "path": str(path), "profile": profile.summary()}
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"profile validate: OK {profile.id} {profile.profile_version} (schema {profile.schema_version})")
    return 0


def command_profile_views(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    try:
        profile, _path = load_current_profile(root)
    except ProfileValidationError as exc:
        print(f"profile views: {exc}", file=sys.stderr)
        return 1
    plan = profile_views_plan(root, profile)
    write_result = None
    if args.write:
        write_result = write_profile_views(root, profile)
        plan = profile_views_plan(root, profile)
    if args.json:
        payload = {"plan": plan, "write": write_result} if write_result is not None else plan
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        mode = "--write" if args.write else "--check"
        print(f"profile views {mode}: {profile.id} {profile.profile_version}")
        print(
            "Summary: "
            f"{plan['summary']['views']} view(s), "
            f"{plan['summary']['actions']} action(s), "
            f"{plan['summary']['blockers']} blocker(s)"
        )
        if plan["blockers"]:
            print("Blockers:")
            for blocker in plan["blockers"]:
                print(f"- {blocker['code']}: {blocker['path']}: {blocker['detail']}")
        elif args.write and write_result is not None:
            print(
                "Write summary: "
                f"{write_result['summary']['written']} written, "
                f"{write_result['summary']['skipped']} skipped, "
                f"{write_result['summary']['errors']} error(s)"
            )
            for item in write_result["written"]:
                print(f"- wrote {item['path']}: {item['detail']}")
            for item in write_result["skipped"]:
                print(f"- skipped {item['path']}: {item['detail']}")
            for item in write_result["errors"]:
                print(f"- error {item['path']}: {item['detail']}")
        elif not plan["actions"]:
            print("Profile-generated views are current.")
        else:
            print("Required view updates:")
            for action in plan["actions"]:
                print(f"- {action['action']}: {action['path']} ({action['reason']})")
    if plan["blockers"]:
        return 1
    if write_result and write_result["errors"]:
        return 1
    if args.check and plan["actions"]:
        return 1
    return 0


def load_target_profile(profile_id: str | None = None) -> tuple[ProfileContract, Path, Path]:
    template = template_source()
    if not template:
        raise ProfileValidationError("no built-in profiles found")
    profiles = built_in_profiles()
    if not profiles:
        raise ProfileValidationError("no built-in profiles found")
    target_id = profile_id or DEFAULT_TEMPLATE_PROFILE_ID
    loaded = profiles.get(target_id)
    if not loaded:
        raise ProfileValidationError(f"unknown built-in profile: {target_id}")
    profile, path = loaded
    return profile, path, template


def command_profile_diff(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    try:
        current, _current_path = load_current_profile(root)
        target, target_path, template = load_target_profile(current.id)
    except ProfileValidationError as exc:
        print(f"profile diff: {exc}", file=sys.stderr)
        return 1
    if args.target_profile_version != target.profile_version:
        print(
            f"profile diff: target profile version '{args.target_profile_version}' is not available; "
            f"available: {target.profile_version}",
            file=sys.stderr,
        )
        return 1
    plan = profile_migration_plan(root, template, current, target, target_path)
    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(f"profile diff: {current.id} {current.profile_version} -> {target.profile_version}")
        if not plan["differences"]:
            print("No profile contract differences detected.")
        else:
            for difference in plan["differences"]:
                print(f"- {difference['field']}: {difference['kind']}")
    return 1 if plan["blockers"] else 0


def command_profile_migrate(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    try:
        current, _current_path = load_optional_current_profile(root)
        target_profile_id = args.profile or (current.id if current else None)
        target, target_path, template = load_target_profile(target_profile_id)
    except ProfileValidationError as exc:
        print(f"profile migrate: {exc}", file=sys.stderr)
        return 1
    plan = profile_migration_plan(root, template, current, target, target_path)
    write_result = None
    if args.write:
        write_result = write_profile_migration(root, template, plan, target, target_path)
    if args.json:
        payload = {"plan": plan, "write": write_result} if write_result is not None else plan
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        current_version = current.profile_version if current else "none"
        mode = "--write" if args.write else "--plan"
        print(f"profile migrate {mode}: {target.id} {current_version} -> {target.profile_version}")
        print(f"Summary: {plan['summary']['actions']} action(s), {plan['summary']['blockers']} blocker(s)")
        if plan["blockers"]:
            print("Blockers:")
            for blocker in plan["blockers"]:
                print(f"- {blocker['code']}: {blocker['detail']}")
        elif args.write and write_result is not None:
            print(
                "Write summary: "
                f"{write_result['summary']['written']} written, "
                f"{write_result['summary']['skipped']} skipped, "
                f"{write_result['summary']['errors']} error(s)"
            )
            for item in write_result["written"]:
                print(f"- wrote {item['path']}: {item['detail']}")
            for item in write_result["skipped"]:
                print(f"- skipped {item['path']}: {item['detail']}")
            for item in write_result["errors"]:
                print(f"- error {item['path']}: {item['detail']}")
        elif not plan["actions"]:
            print("No profile migration actions needed.")
        else:
            print("Planned actions:")
            for action in plan["actions"]:
                print(f"- {action['action']}: {action['path']}")
    if plan["blockers"]:
        return 1
    if write_result and write_result["errors"]:
        return 1
    return 0


def command_init(args: argparse.Namespace) -> int:
    try:
        profile, _profile_path, template = load_target_profile(args.profile)
    except ProfileValidationError as exc:
        print(f"mirrorarc init: {exc}", file=sys.stderr)
        return 1
    target = args.target.expanduser().resolve()
    try:
        ensure_empty_or_missing(target)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    target.mkdir(parents=True, exist_ok=True)
    if profile.id == DEFAULT_TEMPLATE_PROFILE_ID:
        shutil.copytree(template, target, dirs_exist_ok=True)
    else:
        scaffold_profile_vault(target, template, profile, _profile_path)
    print(f"MirrorArc vault created at: {target}")
    print(f"Profile: {profile.id} {profile.profile_version}")
    target_arg = shlex.quote(str(target))
    print("Next (with an installed MirrorArc CLI):")
    print(f"  mirrorarc --root {target_arg} doctor")
    print(f"  mirrorarc --root {target_arg} plan")
    print(f"  mirrorarc --root {target_arg} sync --json")
    print(f"  mirrorarc --root {target_arg} status --json")
    return 0


def catalog_args(args: argparse.Namespace) -> list[str]:
    return (
        (["--json"] if args.json else [])
        + (["--html"] if args.html else [])
        + (["--include-content"] if args.include_content else [])
        + (["--stdout"] if args.stdout else [])
        + (["--check"] if args.check else [])
        + (["--output", str(args.output)] if args.output != Path("CATALOG.md") else [])
        + (["--max-items", str(args.max_items)] if args.max_items != 500 else [])
    )


def command_catalog(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    return catalog_module.main(catalog_args(args), root=root)


def conversion_args(args: argparse.Namespace) -> list[str]:
    return (
        (["--results", str(args.results)] if args.results else [])
        + (["--init-results"] if args.init_results else [])
        + (["--force"] if args.force else [])
        + (["--require-reviewed"] if args.require_reviewed else [])
        + (["--json"] if args.json else [])
        + (["--guide"] if args.guide else [])
        + (
            ["--low-risk-per-format", str(args.low_risk_per_format)]
            if args.low_risk_per_format != 1
            else []
        )
    )


def command_conversion(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    return conversion_module.main(conversion_args(args), root=root)


def command_lint(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    return lint_module.main(root=root)


def review_args(args: argparse.Namespace) -> list[str]:
    return (
        (["--artifact", str(args.artifact)] if args.artifact else [])
        + (["--status", args.status] if args.status else [])
        + (["--reviewer", args.reviewer] if args.reviewer else [])
        + (["--note", args.note] if args.note else [])
        + (["--kind", args.kind] if args.kind else [])
        + (["--json"] if args.json else [])
        + (["--check"] if args.check else [])
    )


def command_review(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    return review_ledger_module.main(review_args(args), root=root)


def recovery_args(args: argparse.Namespace) -> list[str]:
    return (
        (["--json"] if args.json else [])
        + (["--worksheet"] if args.worksheet else [])
        + (["--runbook"] if args.runbook else [])
    )


def command_recovery(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    return recovery_module.main(recovery_args(args), root=root)


def command_m365(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    return m365_module.main(["--json"] if args.json else [], root=root)


def migration_args(args: argparse.Namespace) -> list[str]:
    return (
        (["--json"] if args.json else [])
        + (["--worksheet"] if args.worksheet else [])
        + (["--runbook"] if args.runbook else [])
        + (["--normalize-frontmatter-domains"] if args.normalize_frontmatter_domains else [])
        + (["--apply-markdown-review", str(args.apply_markdown_review)] if args.apply_markdown_review else [])
        + (["--backup-dir", str(args.backup_dir)] if args.backup_dir else [])
        + (["--write"] if args.write else [])
    )


def command_migration(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    return migration_module.main(migration_args(args), root=root)


def command_inventory(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    report = knowledge_inventory_module.build_inventory(root)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(knowledge_inventory_module.render_text(report), end="")
    return 1 if report["errors"] or report["summary"]["unexplained_markdown"] else 0


def command_relationships_refresh(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    result = refresh_relationships(root)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            "relationships refresh: "
            f"artifacts={result['artifacts']} relationships={result['relationships']} "
            f"fingerprint={result['fingerprint']}"
        )
        if result["inventory_errors"]:
            print(f"relationships refresh: inventory warnings={len(result['inventory_errors'])}")
    return 0


def command_relationships_status(args: argparse.Namespace) -> int:
    status = RelationshipStore(args.root.expanduser().resolve()).status()
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print(
            "relationships status: "
            f"artifacts={status['artifacts']['total']} relationships={status['relationships']['total']} "
            f"current={status['relationships']['current']} evidence={status['evidence_anchors']} "
            f"reviews={status['reviews']} invalidations={status['invalidations']}"
        )
    return 0


def command_relationships_export(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    payload = RelationshipStore(root).export(current_only=args.current)
    text_value = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out:
        output = args.out.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text_value, encoding="utf-8")
        print(f"relationships export: wrote {output}")
    else:
        print(text_value, end="")
    return 0


def command_relationships_propose(args: argparse.Namespace) -> int:
    try:
        result = propose_relationship(
            args.root.expanduser().resolve(),
            source_artifact_id=args.source,
            target_artifact_id=args.target,
            relationship_type=args.type,
            evidence_artifact_id=args.evidence_artifact,
            selector_type=args.selector_type,
            selector_value=args.selector,
            excerpt=args.excerpt or "",
            confidence=args.confidence,
            method=args.method,
            method_version=args.method_version,
            model_version=args.model_version or "",
            prompt_version=args.prompt_version or "",
        )
    except RelationshipValidationError as exc:
        print(f"relationships propose: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else f"relationships propose: {result['relationship_id']} state=proposed")
    return 0


def command_relationships_review(args: argparse.Namespace) -> int:
    try:
        result = RelationshipStore(args.root.expanduser().resolve()).review_relationship(
            args.relationship_id,
            reviewer=args.reviewer,
            verdict=args.verdict,
            note=args.note or "",
        )
    except RelationshipValidationError as exc:
        print(f"relationships review: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else f"relationships review: {result['relationship_id']} state={result['state']}")
    return 0


def command_view_list(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    try:
        lenses = load_lenses(root)
        views = KnowledgeViewStore(root).list()
    except (LensDefinitionError, KnowledgeViewError) as exc:
        print(f"view list: {exc}", file=sys.stderr)
        return 1
    payload = {"lenses": lenses, "views": views}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"view list: lenses={len(lenses)} rendered={len(views)}")
        for lens_id, lens in lenses.items():
            count = sum(1 for view in views if view["lens_id"] == lens_id)
            print(f"  - {lens_id}: {lens['purpose']} (rendered={count})")
    return 0


def command_view_render(args: argparse.Namespace) -> int:
    try:
        result = render_lens(args.root.expanduser().resolve(), args.lens_id)
    except (LensDefinitionError, KnowledgeViewError, RelationshipValidationError) as exc:
        print(f"view render: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            f"view render: {result['view_id']} state={result['state']} version={result['version']} "
            f"citations={len(result['citations'])} unchanged={str(result['unchanged']).lower()}"
        )
        print(f"view output: {result['output_path']}")
    return 0


def command_view_pin(args: argparse.Namespace) -> int:
    try:
        result = pin_view(args.root.expanduser().resolve(), args.view_id)
    except KnowledgeViewError as exc:
        print(f"view pin: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else f"view pin: {result['view_id']} -> {result['output_path']}")
    return 0


def command_view_review(args: argparse.Namespace) -> int:
    try:
        result = review_view(args.root.expanduser().resolve(), args.view_id, reviewer=args.reviewer)
    except KnowledgeViewError as exc:
        print(f"view review: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else f"view review: {result['view_id']} state=reviewed")
    return 0


def command_view_promote(args: argparse.Namespace) -> int:
    try:
        result = promote_view(
            args.root.expanduser().resolve(), args.view_id,
            target=args.target, reviewer=args.reviewer, reason=args.reason,
        )
    except KnowledgeViewError as exc:
        print(f"view promote: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else f"view promote: {result['view_id']} -> {result['target']}")
    return 0


def command_view_status(args: argparse.Namespace) -> int:
    status = KnowledgeViewStore(args.root.expanduser().resolve()).status()
    print(json.dumps(status, indent=2, sort_keys=True) if args.json else f"view status: total={status['total']} persistent={status['persistent']} dependencies={status['dependencies']} states={status['by_state']}")
    return 0


def command_context_build(args: argparse.Namespace) -> int:
    try:
        result = build_context(
            args.root.expanduser().resolve(), args.lens_id, mode=args.mode,
            name=args.name or "", purpose=args.purpose or "", query=args.query or "",
            max_tokens=args.max_tokens, max_files=args.max_files,
            max_excerpt_chars=args.max_excerpt_chars,
            permitted_types=args.permitted_type or None,
        )
    except (ContextAssemblyError, ContextStoreError, LensDefinitionError, ProfileValidationError) as exc:
        print(f"context build: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif args.mode == "metadata":
        print(f"context build: metadata items={result['selection_count']} -> {result['output_path']}")
    else:
        print(
            f"context build: dynamic definition={result['definition']['definition_id']} "
            f"current-items={result['resolved']['selection_count']}"
        )
    return 0


def command_context_resolve(args: argparse.Namespace) -> int:
    try:
        result = resolve_dynamic_context(args.root.expanduser().resolve(), args.definition_id)
    except (ContextAssemblyError, ContextStoreError) as exc:
        print(f"context resolve: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else f"context resolve: items={result['selection_count']}")
    return 0


def command_context_freeze(args: argparse.Namespace) -> int:
    try:
        result = freeze_context(
            args.root.expanduser().resolve(), definition_id=args.definition_id or "",
            lens_id=args.lens_id or "", task=args.task,
            name=args.name or "", purpose=args.purpose or "", query=args.query or "",
            max_tokens=args.max_tokens, max_files=args.max_files,
            max_excerpt_chars=args.max_excerpt_chars,
            permitted_types=args.permitted_type or None,
        )
    except (ContextAssemblyError, ContextStoreError, LensDefinitionError, ProfileValidationError) as exc:
        print(f"context freeze: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            f"context freeze: {result['context_id']} included={result['included_count']} "
            f"sensitivity={result['sensitivity']} unchanged={str(result['unchanged']).lower()}"
        )
        print(f"context output: {result['output_path']}")
    return 0


def command_context_status(args: argparse.Namespace) -> int:
    status = ContextStore(args.root.expanduser().resolve()).status(args.context_id)
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        stale = sum(1 for pack in status["packs"] if pack["freshness_state"] == "stale")
        print(f"context status: definitions={len(status['definitions'])} packs={len(status['packs'])} stale={stale}")
        for pack in status["packs"]:
            print(
                f"  - {pack['context_id']}: {pack['mode']} {pack['freshness_state']} "
                f"newer={len(pack['newer_versions'])}"
            )
    return 0


def command_code_doctor(args: argparse.Namespace) -> int:
    report = code_doctor_report(
        args.root.expanduser().resolve(),
        args.repo,
        verbose=args.verbose,
    )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(report["verdict"])
        print(report["message"])
        print(f"Next: {report['next_action']}")
        if report["status"] == "setup-needed":
            print(f"Then retry: {report['retry_command']}")
    return 0 if report["status"] == "ready" else 1


def command_code_analyze(args: argparse.Namespace) -> int:
    from mirrorarc.context_assembly.builder import require_mode
    root = args.root.expanduser().resolve()
    try:
        if args.context:
            require_mode(root, args.context)
        result = analyze_repository(
            root,
            args.repo,
            symbol=args.symbol or "",
            base=args.base or "",
            changed_paths=args.changed_path or [],
        )
        context_result = None
        if args.context == "dynamic":
            context_result = build_dynamic_code_context(root, result)
        elif args.context == "frozen":
            context_result = freeze_code_context(root, result)
    except (CodeIntelligenceError, CodeGraphError, ContextAssemblyError, ContextStoreError) as exc:
        print(f"code analyze: {exc}", file=sys.stderr)
        return 1
    payload = {**result, "context": context_result} if context_result else result
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"Repository evidence ready: {result['configured_repo']} · "
            f"{result['analysis_kind']} · {result['freshness_state']}"
        )
        print(f"Revision: {result['resolved_revision']}")
        print(
            f"Evidence: {len(result['files'])} file(s), "
            f"{len(result['affected_tests'])} candidate affected test(s)"
        )
        if result["warnings"]:
            for warning in result["warnings"]:
                print(f"Warning: {warning}")
        if result["omissions"]:
            print(f"Omissions: {len(result['omissions'])} (use --json for details)")
        if context_result:
            if args.context == "dynamic":
                print(f"Dynamic context: {context_result['definition']['definition_id']}")
            else:
                print(f"Frozen context: {context_result['context_id']} -> {context_result['output_path']}")
        print(f"Next: {result['next_action']['command']}")
    return 0


def command_code_status(args: argparse.Namespace) -> int:
    try:
        report = code_status_report(args.root.expanduser().resolve(), args.repo)
    except CodeIntelligenceError as exc:
        print(f"code status: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        if not report["items"]:
            print("No governed repositories are configured.")
        for item in report["items"]:
            print(f"{item['configured_repo']}: {item['freshness_state']}")
            if item["reason"]:
                print(f"  {item['reason']}")
            print(f"  Next: {item['next_action']}")
    return 1 if report["summary"]["attention"] else 0


def command_document(args: argparse.Namespace) -> int:
    from mirrorarc.document_intelligence.adapter import DocumentIntelligenceError, doctor
    from mirrorarc.document_intelligence.service import ask_document, index_document, status_report

    root = args.root.expanduser().resolve()
    try:
        if args.document_command == 'doctor':
            result = doctor()
        elif args.document_command == 'index':
            if args.context:
                from mirrorarc.context_assembly.builder import require_mode
                require_mode(root, args.context)
            result = index_document(root, args.source, model_assisted=args.model_assisted,
                                    allow_model=args.allow_model, index_mode=args.mode, force=args.force)
            if args.context:
                from mirrorarc.document_intelligence.context import build_document_context
                result['context'] = build_document_context(root, args.source, args.page or [], mode=args.context)
        elif args.document_command == 'ask':
            result = ask_document(root, args.source, args.question, allow_model=args.allow_model)
        else:
            result = status_report(root, args.source)
    except (DocumentIntelligenceError, ContextAssemblyError, OSError) as exc:
        if args.json:
            print(json.dumps({'ok': False, 'error': str(exc)}, sort_keys=True))
        else:
            print(f'document {args.document_command}: {exc}', file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, sort_keys=True, ensure_ascii=False, indent=2))
    elif args.document_command == 'doctor':
        print(f"{result['status']}\n{result['next_action']}")
    elif args.document_command == 'index':
        print(f"Document structure ready: {result['page_count']} pages · {result['method']}")
        print(f"Source: {result['source_path']}\nSHA-256: {result['source_hash']}")
        if args.context == 'dynamic':
            print(f"Saved page selection: {result['context']['definition']['definition_id']}")
        elif args.context == 'frozen':
            print(f"Frozen evidence: {root / result['context']['output_path']}")
        print('Next: review the structure before approving model-assisted questions.')
    elif args.document_command == 'ask':
        print('Unreviewed answer candidate\n')
        print(result['answer'])
        print('\nCitation addresses checked; claim support still needs human review.')
        print(f"Candidate saved: {root / result['output_path']}")
        print('Next: generate a local Catalog with catalog --html --include-content, then open Document metadata → Answer review.')
    else:
        for item in result['items']:
            print(f"{item['source_id']}: {item['freshness_state']} — {item.get('reason', item['source_path'])}")
        if not result['items']:
            print('No registered PDFs. Run mirrorarc sync on a copied vault first.')
    return 1 if result.get('ready') is False else 0


def overlap_args(args: argparse.Namespace) -> list[str]:
    return (
        (["--json"] if args.json else [])
        + (["--worksheet"] if args.worksheet else [])
        + (["--max-pairs", str(args.max_pairs)] if args.max_pairs != 40 else [])
    )


def command_overlap(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    return overlap_module.main(overlap_args(args), root=root)


def benchmark_args(args: argparse.Namespace) -> list[str]:
    return (
        (["--compact-pack", str(args.compact_pack)] if args.compact_pack else [])
        + (["--task-retrieval"] if args.task_retrieval else [])
        + (["--tasks", str(args.tasks)] if args.tasks else [])
        + (["--results", str(args.results)] if args.results else [])
        + (["--init-tasks"] if args.init_tasks else [])
        + (["--init-results"] if args.init_results else [])
        + (["--force"] if args.force else [])
        + (["--scaffold-sources", str(args.scaffold_sources)] if args.scaffold_sources != 5 else [])
        + (["--scaffold-curated", str(args.scaffold_curated)] if args.scaffold_curated != 5 else [])
        + (["--worksheet"] if args.worksheet else [])
        + (["--require-generated"] if args.require_generated else [])
        + (["--require-results"] if args.require_results else [])
        + (["--require-citations"] if args.require_citations else [])
        + (["--require-prompt-safety"] if args.require_prompt_safety else [])
        + (["--json"] if args.json else [])
    )


def command_benchmark(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    return benchmark_module.main(benchmark_args(args), root=root)


def pilot_args(args: argparse.Namespace) -> list[str]:
    return (
        (["--json"] if args.json else [])
        + (["--worksheet"] if args.worksheet else [])
    )


def command_pilot(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    return pilot_module.main(pilot_args(args), root=root)


def sandbox_args(args: argparse.Namespace) -> list[str]:
    return (
        (["--source-root", str(args.source_root)] if args.source_root else [])
        + (["--json"] if args.json else [])
    )


def command_sandbox(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    return sandbox_module.main(sandbox_args(args), root=root)


def command_doctor(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    return doctor_module.main(root=root, json_output=args.json)


def run_module_json(func, argv: list[str], **kwargs) -> tuple[int, dict]:
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        status = int(func(argv, **kwargs))
    text = stream.getvalue().strip()
    if not text:
        return status, {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return status or 1, {"raw_output": text, "error": "invalid-json-output"}
    if isinstance(payload, dict):
        return status, payload
    return status, {"payload": payload}


def repo_config(root: Path) -> Path:
    return root / "tools" / "repos.yml"


def command_plan(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    status = office_sync_module.main(["--plan"], default_root=root)
    config = repo_config(root)
    if config.exists():
        status = max(status, repo_sync_module.main(["--plan"], default_root=root, default_config=config))
    else:
        print("mirrorarc plan: no tools/repos.yml found; repo plan skipped")
    return status


def command_sync(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    if getattr(args, "changed", False):
        holder = args.holder or f"cli-{os.getpid()}"
        try:
            payload = changed_sync_module.sync_changed(
                root,
                holder,
                retry_failed=args.retry_failed,
                max_events=args.max_events,
                lease_ttl_seconds=args.lease_ttl_seconds,
            )
        except (
            journal_module.JournalError,
            reconcile_module.ReconciliationError,
            replay_module.ReplayError,
        ) as exc:
            print(f"sync --changed: {exc}", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            replay_payload = payload["replay"]
            print(
                "mirrorarc sync --changed: "
                f"queued {payload['events_queued']} event(s), "
                f"processed {payload['processed']} event(s)"
            )
            counts = payload["finish_counts"]
            print(
                "finish counts: "
                f"applied={counts['applied']} "
                f"review-required={counts['review-required']} "
                f"failed={counts['failed']}"
            )
            print(
                "candidate full hashes: "
                f"{payload['reconciliation']['full_hashes']} "
                f"({payload['reconciliation']['bytes_hashed']} bytes)"
            )
            if not replay_payload["acquired"]:
                lease = replay_payload["lease"]
                print(f"worker: locked by {lease['holder']} until {lease['expires_at']}")
        if not payload["replay"]["acquired"]:
            return 1
        return 1 if payload["finish_counts"]["failed"] else 0

    if any(
        (
            getattr(args, "retry_failed", False),
            getattr(args, "max_events", None) is not None,
            getattr(args, "holder", None),
        )
    ):
        print("sync: --retry-failed, --max-events, and --holder require --changed", file=sys.stderr)
        return 2
    if args.json:
        office_status, office_payload = run_module_json(
            office_sync_module.main,
            ["--json"],
            default_root=root,
        )
        repo_status, repo_payload = run_module_json(
            repo_sync_module.main,
            ["--json"],
            default_root=root,
            default_config=repo_config(root),
        )
        payload = {
            "mode": "sync",
            "root": str(root),
            "office": office_payload,
            "repos": repo_payload,
            "exit_codes": {"office": office_status, "repos": repo_status},
        }
        from mirrorarc.relationships.invalidation import reconcile_derived_state
        payload["derived_invalidation"] = reconcile_derived_state(root)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return office_status or repo_status
    office = office_sync_module.main([], default_root=root)
    repos = repo_sync_module.main([], default_root=root, default_config=repo_config(root))
    from mirrorarc.relationships.invalidation import reconcile_derived_state
    reconcile_derived_state(root)
    return office or repos


def _print_watch_payload(payload: dict, holder: str, *, json_output: bool, label: str) -> int:
    if json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"mirrorarc {label}: "
            f"queued {payload['events_queued']} event(s), "
            f"processed {payload['processed']} event(s)"
        )
        print(f"startup reconciliation: {'yes' if payload['reconcile_on_start'] else 'no'}")
        print(f"feed events queued: {payload['feed_events_queued']}")
        counts = payload["finish_counts"]
        print(
            "finish counts: "
            f"applied={counts['applied']} "
            f"review-required={counts['review-required']} "
            f"failed={counts['failed']}"
        )
        lease = payload["replay"]["lease"]
        if payload["replay"]["acquired"]:
            print(f"worker: acquired by {holder} until {lease['expires_at']}")
        else:
            print(f"worker: locked by {lease['holder']} until {lease['expires_at']}")
    if not payload["replay"]["acquired"]:
        return 1
    return 1 if payload["finish_counts"]["failed"] else 0


def _watch_once_payload(args: argparse.Namespace, root: Path, holder: str, observed: list | None = None) -> dict:
    return watch_module.watch_once(
        root,
        holder,
        observed_feed=feed_module.StaticChangeFeed(observed or []) if observed is not None else None,
        retry_failed=args.retry_failed,
        max_events=args.max_events,
        lease_ttl_seconds=args.lease_ttl_seconds,
        reconcile_on_start=not args.no_reconcile_on_start,
    )


def command_watch(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    if not args.once and not args.native:
        print(
            "watch: choose --once for deterministic startup replay or --native for optional "
            "watchdog-backed continuous capture",
            file=sys.stderr,
        )
        return 2
    holder = args.holder or f"watch-{os.getpid()}"
    if args.once:
        try:
            payload = _watch_once_payload(args, root, holder)
        except (
            journal_module.JournalError,
            reconcile_module.ReconciliationError,
            replay_module.ReplayError,
            watch_module.WatchError,
        ) as exc:
            print(f"watch: {exc}", file=sys.stderr)
            return 1
        return _print_watch_payload(payload, holder, json_output=args.json, label="watch --once")

    if args.cycles is not None and args.cycles < 1:
        print("watch --native: --cycles must be positive when provided", file=sys.stderr)
        return 2
    if args.flush_interval_seconds <= 0:
        print("watch --native: --flush-interval-seconds must be positive", file=sys.stderr)
        return 2
    try:
        observer, handler, roots = native_watch_module.build_watchdog_observer(root)
    except native_watch_module.NativeWatchError as exc:
        print(f"watch --native: {exc}", file=sys.stderr)
        return 2
    if not args.json:
        print("mirrorarc watch --native: watching " + ", ".join(path.relative_to(root).as_posix() for path in roots))
    observer.start()
    exit_code = 0
    cycles = 0
    try:
        while True:
            time.sleep(args.flush_interval_seconds)
            cycles += 1
            observed = handler.drain()
            try:
                payload = _watch_once_payload(
                    args,
                    root,
                    holder,
                    observed=observed,
                )
            except (
                journal_module.JournalError,
                reconcile_module.ReconciliationError,
                replay_module.ReplayError,
                watch_module.WatchError,
            ) as exc:
                print(f"watch --native: {exc}", file=sys.stderr)
                exit_code = 1
                break
            exit_code = _print_watch_payload(
                payload,
                holder,
                json_output=args.json,
                label=f"watch --native cycle {cycles}",
            )
            if exit_code:
                break
            args.no_reconcile_on_start = True
            if args.cycles is not None and cycles >= args.cycles:
                break
    except KeyboardInterrupt:
        if not args.json:
            print("mirrorarc watch --native: stopped")
    finally:
        observer.stop()
        observer.join()
    return exit_code


def command_status(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    if args.json:
        office_status, office_payload = run_module_json(
            office_sync_module.main,
            ["--status", "--json"],
            default_root=root,
        )
        repo_status, repo_payload = run_module_json(
            repo_sync_module.main,
            ["--status", "--json"],
            default_root=root,
            default_config=repo_config(root),
        )
        payload = {
            "mode": "status",
            "root": str(root),
            "office": office_payload,
            "repos": repo_payload,
            "exit_codes": {"office": office_status, "repos": repo_status},
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return office_status or repo_status
    status = office_sync_module.main(["--status"], default_root=root)
    config = repo_config(root)
    if config.exists():
        status = max(status, repo_sync_module.main(["--status"], default_root=root, default_config=config))
    else:
        print("mirrorarc status: no tools/repos.yml found; repo status skipped")
    return status


def command_journal_status(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    try:
        payload = journal_module.journal_status(root, initialize_state=args.init)
    except journal_module.JournalError as exc:
        print(f"journal status: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    print(f"mirrorarc journal status: {payload['state_path']}")
    print(f"state: {'initialized' if payload['initialized'] else 'not initialized'}")
    schema = payload.get("schema_version")
    schema_text = str(schema) if schema is not None else "unknown"
    if not payload.get("schema_supported", True):
        schema_text += " (unsupported by this MirrorArc)"
    print(f"schema: {schema_text}")
    for warning in payload.get("warnings", []):
        print(f"warning: {warning}")
    print(f"last event sequence: {payload['last_event_sequence']}")
    print(f"last observed sequence: {payload['last_observed_sequence']}")
    print(f"last applied sequence: {payload['last_applied_sequence']}")
    print(
        "counts: "
        f"queued={payload['queued_count']} "
        f"processing={payload['processing_count']} "
        f"failed={payload['failed_count']} "
        f"review-required={payload['review_required_count']}"
    )
    print(f"last reconciliation: {payload['last_reconciliation'] or 'never'}")
    worker = payload["worker"]
    if worker["locked"]:
        print(f"worker: locked by {worker['holder']} until {worker['expires_at']}")
    elif worker.get("stale"):
        print(f"worker: stale lease from {worker['holder']} expired at {worker['expires_at']}")
    else:
        print("worker: unlocked")
    return 0


def command_journal_replay(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    holder = args.holder or f"cli-{os.getpid()}"
    try:
        payload = replay_module.replay_journal(
            root,
            holder,
            retry_failed=args.retry_failed,
            max_events=args.max_events,
            lease_ttl_seconds=args.lease_ttl_seconds,
        )
    except (journal_module.JournalError, replay_module.ReplayError) as exc:
        print(f"journal replay: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"mirrorarc journal replay: processed {payload['processed']} event(s)")
        print(f"recovered processing: {len(payload['recovered_processing'])}")
        print(f"retried failed: {len(payload['retried_failed'])}")
        counts = payload["finish_counts"]
        print(
            "finish counts: "
            f"applied={counts['applied']} "
            f"review-required={counts['review-required']} "
            f"failed={counts['failed']}"
        )
        lease = payload["lease"]
        if payload["acquired"]:
            print(f"worker: acquired by {holder} until {lease['expires_at']}")
        else:
            print(f"worker: locked by {lease['holder']} until {lease['expires_at']}")
    if not payload["acquired"]:
        return 1
    return 1 if payload["finish_counts"]["failed"] else 0


def command_reconcile(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    try:
        payload = reconcile_module.reconcile_workspace(root)
    except (journal_module.JournalError, reconcile_module.ReconciliationError) as exc:
        print(f"reconcile: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    print(f"mirrorarc reconcile: queued {payload['events_queued']} event(s)")
    print(f"scanned sources: {payload['scanned_sources']}")
    print(f"manifest records: {payload['manifest_records']}")
    print(
        "event counts: "
        f"created={payload['event_counts']['created']} "
        f"modified={payload['event_counts']['modified']} "
        f"moved={payload['event_counts']['moved']} "
        f"deleted={payload['event_counts']['deleted']} "
        f"reconcile-required={payload['event_counts']['reconcile-required']}"
    )
    print(f"existing unresolved events skipped: {payload['events_skipped']}")
    print(f"candidate full hashes: {payload['full_hashes']} ({payload['bytes_hashed']} bytes)")
    print(f"last reconciliation: {payload['reconciled_at']}")
    return 0


def command_migrate_annotations(args: argparse.Namespace) -> int:
    root = args.root.expanduser().resolve()
    plan = annotation_migration_plan(root)
    if args.write:
        result = write_annotation_sidecars(root, plan)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            summary = result["summary"]
            print(
                "migrate annotations --write: "
                f"{summary['written']} written, {summary['blockers']} blocker(s)"
            )
            if result["blockers"]:
                print("Blockers:")
                for blocker in result["blockers"]:
                    print(f"- {blocker['code']}: {blocker['detail']}")
            elif not result["written"]:
                print("No mirror annotations need migration.")
            else:
                for item in result["written"]:
                    print(f"- {item['mirror_path']} -> {item['sidecar_path']}")
        return 1 if result["blockers"] else 0

    payload = public_plan(plan)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        summary = payload["summary"]
        print(
            "migrate annotations --plan: "
            f"{summary['actions']} action(s), {summary['blockers']} blocker(s), "
            f"{summary['already_migrated']} already migrated"
        )
        if payload["blockers"]:
            print("Blockers:")
            for blocker in payload["blockers"]:
                print(f"- {blocker['code']}: {blocker['detail']}")
        elif not payload["actions"]:
            print("No mirror annotations need migration.")
        else:
            print("Planned actions:")
            for action in payload["actions"]:
                print(f"- {action['mirror_path']} -> {action['sidecar_path']}")
    return 1 if payload["blockers"] else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MirrorArc command-line interface.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Vault root for plan/sync/status/lint/doctor.")
    parser.add_argument("--version", action="version", version=f"mirrorarc {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Scaffold a new MirrorArc vault from the template.")
    init.add_argument(
        "--profile",
        default=DEFAULT_TEMPLATE_PROFILE_ID,
        help="Official profile to initialize.",
    )
    init.add_argument("target", type=Path)
    init.set_defaults(func=command_init)
    profile = sub.add_parser("profile", help="Inspect and validate MirrorArc profile contracts.")
    profile_sub = profile.add_subparsers(dest="profile_command", required=True)
    profile_list = profile_sub.add_parser("list", help="List built-in profiles.")
    profile_list.add_argument("--json", action="store_true", help="Print machine-readable profile summaries.")
    profile_list.set_defaults(func=command_profile_list)
    profile_show = profile_sub.add_parser("show", help="Show a built-in or current-vault profile.")
    profile_show.add_argument(
        "profile_id",
        nargs="?",
        help="Built-in profile ID. Omit to show --root/_meta/profile.yml.",
    )
    profile_show.add_argument("--json", action="store_true", help="Print machine-readable profile details.")
    profile_show.set_defaults(func=command_profile_show)
    profile_validate = profile_sub.add_parser("validate", help="Validate a profile contract.")
    profile_validate.add_argument("--path", type=Path, help="Profile YAML path. Defaults to --root/_meta/profile.yml.")
    profile_validate.add_argument("--json", action="store_true", help="Print machine-readable validation result.")
    profile_validate.set_defaults(func=command_profile_validate)
    profile_views = profile_sub.add_parser("views", help="Check or regenerate profile-owned view files.")
    profile_views_mode = profile_views.add_mutually_exclusive_group(required=True)
    profile_views_mode.add_argument("--check", action="store_true", help="Fail if generated profile views are stale.")
    profile_views_mode.add_argument("--write", action="store_true", help="Regenerate profile-owned view files.")
    profile_views.add_argument("--json", action="store_true", help="Print machine-readable view generation output.")
    profile_views.set_defaults(func=command_profile_views)
    profile_diff = profile_sub.add_parser("diff", help="Compare current vault profile with a built-in target version.")
    profile_diff.add_argument("target_profile_version", help="Target built-in profile version, for example 0.1.0.")
    profile_diff.add_argument("--json", action="store_true", help="Print machine-readable diff and migration plan.")
    profile_diff.set_defaults(func=command_profile_diff)
    profile_migrate = profile_sub.add_parser("migrate", help="Plan or apply safe profile migration work.")
    profile_migrate_mode = profile_migrate.add_mutually_exclusive_group(required=True)
    profile_migrate_mode.add_argument("--plan", action="store_true", help="Print a read-only migration plan.")
    profile_migrate_mode.add_argument(
        "--write",
        action="store_true",
        help="Create missing shared/folder-plan directories and copy missing packaged profile files without overwriting.",
    )
    profile_migrate.add_argument(
        "--profile",
        help="Built-in target profile ID. Defaults to the current vault profile or the packaged default.",
    )
    profile_migrate.add_argument("--json", action="store_true", help="Print machine-readable migration plan.")
    profile_migrate.set_defaults(func=command_profile_migrate)
    migrate = sub.add_parser("migrate", help="Run package-owned MirrorArc migrations.")
    migrate_sub = migrate.add_subparsers(dest="migrate_command", required=True)
    annotations = migrate_sub.add_parser(
        "annotations",
        help="Move human mirror annotations into source-ID-keyed sidecars.",
    )
    annotations_mode = annotations.add_mutually_exclusive_group(required=True)
    annotations_mode.add_argument("--plan", action="store_true", help="Print a read-only annotation migration plan.")
    annotations_mode.add_argument("--write", action="store_true", help="Write annotation sidecars without editing mirrors.")
    annotations.add_argument("--json", action="store_true", help="Print machine-readable migration output.")
    annotations.set_defaults(func=command_migrate_annotations)
    sub.add_parser("plan", help="Inventory sources and proposed mirror actions without writing.").set_defaults(func=command_plan)
    inventory = sub.add_parser("inventory", help="Report source/L1/L2 counts and anti-proliferation invariants.")
    inventory.add_argument("--json", action="store_true", help="Print machine-readable knowledge inventory.")
    inventory.set_defaults(func=command_inventory)
    relationships = sub.add_parser("relationships", help="Build, inspect, propose, and review ledger relationships.")
    relationships_sub = relationships.add_subparsers(dest="relationships_command", required=True)
    relationships_refresh = relationships_sub.add_parser("refresh", help="Rebuild deterministic relationships from current governed state.")
    relationships_refresh.add_argument("--json", action="store_true")
    relationships_refresh.set_defaults(func=command_relationships_refresh)
    relationships_status = relationships_sub.add_parser("status", help="Report relationship/evidence/review counts.")
    relationships_status.add_argument("--json", action="store_true")
    relationships_status.set_defaults(func=command_relationships_status)
    relationships_export = relationships_sub.add_parser("export", help="Export structured ledger metadata without source bodies.")
    relationships_export.add_argument("--current", action="store_true", help="Exclude rejected and invalidated relationships.")
    relationships_export.add_argument("--out", type=Path, help="Optional JSON output path.")
    relationships_export.set_defaults(func=command_relationships_export)
    relationships_propose = relationships_sub.add_parser("propose", help="Add an evidence-backed semantic proposal.")
    relationships_propose.add_argument("--source", required=True)
    relationships_propose.add_argument("--target", required=True)
    relationships_propose.add_argument("--type", required=True)
    relationships_propose.add_argument("--evidence-artifact", required=True)
    relationships_propose.add_argument("--selector-type", default="line")
    relationships_propose.add_argument("--selector", required=True)
    relationships_propose.add_argument("--excerpt")
    relationships_propose.add_argument("--confidence", type=float)
    relationships_propose.add_argument("--method", default="rule-proposal")
    relationships_propose.add_argument("--method-version", default="1")
    relationships_propose.add_argument("--model-version")
    relationships_propose.add_argument("--prompt-version")
    relationships_propose.add_argument("--json", action="store_true")
    relationships_propose.set_defaults(func=command_relationships_propose)
    relationships_review = relationships_sub.add_parser("review", help="Accept or reject a semantic proposal with named review.")
    relationships_review.add_argument("relationship_id")
    relationships_review.add_argument("--reviewer", required=True)
    relationships_review.add_argument("--verdict", choices=["accepted", "rejected"], required=True)
    relationships_review.add_argument("--note")
    relationships_review.add_argument("--json", action="store_true")
    relationships_review.set_defaults(func=command_relationships_review)
    view = sub.add_parser("view", help="List, render, persist, review, and promote L2 knowledge views.")
    view_sub = view.add_subparsers(dest="view_command", required=True)
    view_list = view_sub.add_parser("list", help="List profile lenses and rendered view state.")
    view_list.add_argument("--json", action="store_true")
    view_list.set_defaults(func=command_view_list)
    view_render = view_sub.add_parser("render", help="Render one deterministic many-to-few lens.")
    view_render.add_argument("lens_id")
    view_render.add_argument("--json", action="store_true")
    view_render.set_defaults(func=command_view_render)
    view_pin = view_sub.add_parser("pin", help="Persist a generated view without accepting it as reviewed.")
    view_pin.add_argument("view_id")
    view_pin.add_argument("--json", action="store_true")
    view_pin.set_defaults(func=command_view_pin)
    view_review = view_sub.add_parser("review", help="Persist and mark a generated/stale view reviewed.")
    view_review.add_argument("view_id")
    view_review.add_argument("--reviewer", required=True)
    view_review.add_argument("--json", action="store_true")
    view_review.set_defaults(func=command_view_review)
    view_promote = view_sub.add_parser("promote", help="Explicitly promote a reviewed view into a new authoritative record.")
    view_promote.add_argument("view_id")
    view_promote.add_argument("--target", type=Path, required=True)
    view_promote.add_argument("--reviewer", required=True)
    view_promote.add_argument("--reason", required=True)
    view_promote.add_argument("--json", action="store_true")
    view_promote.set_defaults(func=command_view_promote)
    view_status = view_sub.add_parser("status", help="Report L2 state and dependency counts.")
    view_status.add_argument("--json", action="store_true")
    view_status.set_defaults(func=command_view_status)
    context = sub.add_parser("context", help="Build metadata selections, dynamic definitions, and frozen offline packs.")
    context_sub = context.add_subparsers(dest="context_command", required=True)
    context_build = context_sub.add_parser("build", help="Build a metadata-only selection or save a dynamic definition.")
    context_build.add_argument("--lens", dest="lens_id", required=True)
    context_build.add_argument("--mode", choices=["metadata", "dynamic"], default="dynamic")
    context_build.add_argument("--name")
    context_build.add_argument("--purpose")
    context_build.add_argument("--query", help="Opt-in task query over current authoritative text and L1.")
    context_build.add_argument("--max-tokens", type=int)
    context_build.add_argument("--max-files", type=int)
    context_build.add_argument("--max-excerpt-chars", type=int)
    context_build.add_argument("--permitted-type", action="append", choices=sorted(["source", "native-source", "repository", "knowledge-view"]))
    context_build.add_argument("--json", action="store_true")
    context_build.set_defaults(func=command_context_build)
    context_resolve = context_sub.add_parser("resolve", help="Resolve a saved dynamic definition against current governed state.")
    context_resolve.add_argument("definition_id")
    context_resolve.add_argument("--json", action="store_true")
    context_resolve.set_defaults(func=command_context_resolve)
    context_freeze = context_sub.add_parser("freeze", help="Create an immutable, content-inclusive offline context pack.")
    context_freeze_source = context_freeze.add_mutually_exclusive_group(required=True)
    context_freeze_source.add_argument("--definition", dest="definition_id")
    context_freeze_source.add_argument("--lens", dest="lens_id")
    context_freeze.add_argument("--task", default="Use the cited evidence to complete the declared purpose offline.")
    context_freeze.add_argument("--name")
    context_freeze.add_argument("--purpose")
    context_freeze.add_argument("--query", help="Opt-in task query; saved definitions preserve their original query.")
    context_freeze.add_argument("--max-tokens", type=int)
    context_freeze.add_argument("--max-files", type=int)
    context_freeze.add_argument("--max-excerpt-chars", type=int)
    context_freeze.add_argument("--permitted-type", action="append", choices=sorted(["source", "native-source", "repository", "knowledge-view"]))
    context_freeze.add_argument("--json", action="store_true")
    context_freeze.set_defaults(func=command_context_freeze)
    context_status = context_sub.add_parser("status", help="Report context definitions, packs, and newer source versions.")
    context_status.add_argument("context_id", nargs="?")
    context_status.add_argument("--json", action="store_true")
    context_status.set_defaults(func=command_context_status)
    code = sub.add_parser("code", help="Inspect optional, revision-bound repository evidence.")
    code_sub = code.add_subparsers(dest="code_command", required=True)
    code_doctor = code_sub.add_parser("doctor", help="Check whether local repository analysis is ready.")
    code_doctor.add_argument("--repo", help="Optional repository ID when more than one repository is configured.")
    code_doctor.add_argument("--json", action="store_true", help="Print stable machine-readable readiness output.")
    code_doctor.add_argument("--verbose", action="store_true", help="Include provider path and managed environment diagnostics.")
    code_doctor.set_defaults(func=command_code_doctor)
    code_analyze = code_sub.add_parser("analyze", help="Analyze one governed repository snapshot.")
    code_analyze.add_argument("--repo", required=True, help="Repository ID from tools/repos.yml or the repository manifest.")
    code_analyze.add_argument("--symbol", help="Inspect one symbol and its bounded call and impact evidence.")
    code_analyze.add_argument("--base", help="Inspect changed paths since a local Git base ref.")
    code_analyze.add_argument(
        "--changed-path",
        action="append",
        help="Inspect one changed repository path; repeat for additional paths.",
    )
    code_analyze.add_argument(
        "--context",
        choices=["dynamic", "frozen"],
        help="Also create governed dynamic or frozen context from the bounded code evidence.",
    )
    code_analyze.add_argument("--json", action="store_true", help="Print stable machine-readable analysis output.")
    code_analyze.set_defaults(func=command_code_analyze)
    code_status = code_sub.add_parser("status", help="Report current, stale, failed, or missing repository analysis.")
    code_status.add_argument("--repo", help="Optional repository ID; defaults to all configured repositories.")
    code_status.add_argument("--json", action="store_true", help="Print stable machine-readable status output.")
    code_status.set_defaults(func=command_code_status)
    document = sub.add_parser('document', help='Inspect optional PageIndex PDF structure and cited answer candidates.')
    document_sub = document.add_subparsers(dest='document_command', required=True)
    document_doctor = document_sub.add_parser('doctor', help='Check the isolated optional PageIndex runtime.')
    document_doctor.add_argument('--json', action='store_true')
    document_doctor.set_defaults(func=command_document)
    document_index = document_sub.add_parser('index', help='Index one registered PDF; model-free by default.')
    document_index.add_argument('--source', required=True, help='Source ID from mirrorarc status --json.')
    document_index.add_argument('--model-assisted', action='store_true', help='Use the explicitly configured model for structure and summaries.')
    document_index.add_argument('--allow-model', action='store_true', help='Approve content transfer to the configured model for this operation.')
    document_index.add_argument('--mode', choices=['flash', 'standard'], default='flash')
    document_index.add_argument('--force', action='store_true', help='Rebuild even if source and settings match; model-assisted rebuilding can incur charges.')
    document_index.add_argument('--context', choices=['dynamic', 'frozen'], help='Also export selected physical PDF pages under current context policy.')
    document_index.add_argument('--page', action='append', type=int, help='Physical PDF page for context; repeat for more pages.')
    document_index.add_argument('--json', action='store_true')
    document_index.set_defaults(func=command_document)
    document_ask = document_sub.add_parser('ask', help='Generate an unreviewed answer with checked page addresses using an approved model.')
    document_ask.add_argument('--source', required=True)
    document_ask.add_argument('--question', required=True)
    document_ask.add_argument('--allow-model', action='store_true')
    document_ask.add_argument('--json', action='store_true')
    document_ask.set_defaults(func=command_document)
    document_status = document_sub.add_parser('status', help='Check indexed PDFs against current source bytes.')
    document_status.add_argument('--source')
    document_status.add_argument('--json', action='store_true')
    document_status.set_defaults(func=command_document)
    sync = sub.add_parser("sync", help="Run Office/repo full sync or journaled changed-file sync.")
    sync_mode = sync.add_mutually_exclusive_group()
    sync_mode.add_argument("--changed", action="store_true", help="Run journaled changed-file sync.")
    sync_mode.add_argument("--full", action="store_true", help="Run the full Office/repo sync path.")
    sync.add_argument("--holder", help="Worker lease holder ID for --changed.")
    sync.add_argument("--retry-failed", action="store_true", help="Retry failed journal events during --changed.")
    sync.add_argument("--max-events", type=int, help="Maximum events to process during --changed.")
    sync.add_argument(
        "--lease-ttl-seconds",
        type=int,
        default=300,
        help="Worker lease time-to-live in seconds for --changed.",
    )
    sync.add_argument("--json", action="store_true", help="Print machine-readable sync results.")
    sync.set_defaults(func=command_sync)
    watch = sub.add_parser("watch", help="Run journaled watch orchestration.")
    watch_mode = watch.add_mutually_exclusive_group()
    watch_mode.add_argument(
        "--once",
        action="store_true",
        help="Run one startup reconciliation/feed replay cycle and exit.",
    )
    watch_mode.add_argument(
        "--native",
        action="store_true",
        help="Continuously capture native filesystem events with the optional watchdog extra.",
    )
    watch.add_argument(
        "--no-reconcile-on-start",
        action="store_true",
        help="Skip startup reconciliation for this watch run.",
    )
    watch.add_argument("--holder", help="Worker lease holder ID for watch replay.")
    watch.add_argument("--retry-failed", action="store_true", help="Retry failed journal events during watch replay.")
    watch.add_argument("--max-events", type=int, help="Maximum events to process during each watch replay.")
    watch.add_argument("--cycles", type=int, help="Maximum native watch flush cycles before exiting.")
    watch.add_argument(
        "--flush-interval-seconds",
        type=float,
        default=2.0,
        help="Seconds between native watch queue flushes.",
    )
    watch.add_argument(
        "--lease-ttl-seconds",
        type=int,
        default=300,
        help="Worker lease time-to-live in seconds for watch replay.",
    )
    watch.add_argument("--json", action="store_true", help="Print machine-readable watch results.")
    watch.set_defaults(func=command_watch)
    status = sub.add_parser("status", help="Report manifest-backed lifecycle status.")
    status.add_argument("--json", action="store_true", help="Print machine-readable lifecycle status.")
    status.set_defaults(func=command_status)
    journal = sub.add_parser("journal", help="Inspect local journaled materialization state.")
    journal_sub = journal.add_subparsers(dest="journal_command", required=True)
    journal_status = journal_sub.add_parser("status", help="Report local journal queue and worker state.")
    journal_status.add_argument("--init", action="store_true", help="Initialize local journal state if missing.")
    journal_status.add_argument("--json", action="store_true", help="Print machine-readable journal status.")
    journal_status.set_defaults(func=command_journal_status)
    journal_replay = journal_sub.add_parser("replay", help="Replay recoverable local journal work.")
    journal_replay.add_argument(
        "--holder",
        help="Worker lease holder ID. Defaults to a process-scoped CLI holder.",
    )
    journal_replay.add_argument(
        "--retry-failed",
        action="store_true",
        help="Requeue failed events before replaying. Interrupted processing events are always recovered.",
    )
    journal_replay.add_argument("--max-events", type=int, help="Maximum number of events to process.")
    journal_replay.add_argument(
        "--lease-ttl-seconds",
        type=int,
        default=300,
        help="Worker lease time-to-live in seconds.",
    )
    journal_replay.add_argument("--json", action="store_true", help="Print machine-readable replay results.")
    journal_replay.set_defaults(func=command_journal_replay)
    reconcile = sub.add_parser("reconcile", help="Queue missed journal events from source/manifest state.")
    reconcile.add_argument("--json", action="store_true", help="Print machine-readable reconciliation results.")
    reconcile.set_defaults(func=command_reconcile)
    doctor = sub.add_parser("doctor", help="Check required files, Python version, and dependencies.")
    doctor.add_argument("--json", action="store_true", help="Print machine-readable doctor results.")
    doctor.set_defaults(func=command_doctor)
    sub.add_parser("lint", help="Run vault health checks.").set_defaults(func=command_lint)
    overlap = sub.add_parser("overlap", help=experimental_help("Print a read-only overlap threshold calibration report."))
    overlap_output = overlap.add_mutually_exclusive_group()
    overlap_output.add_argument("--json", action="store_true", help="Print machine-readable overlap calibration JSON.")
    overlap_output.add_argument("--worksheet", action="store_true", help="Print a Markdown calibration worksheet.")
    overlap.add_argument("--max-pairs", type=int, default=40, help="Maximum current/near-miss pairs to print.")
    overlap.set_defaults(func=command_overlap)
    benchmark = sub.add_parser(
        "benchmark",
        help="Validate the agent-readiness benchmark task pack; experimental scaffold helpers remain unstable.",
    )
    benchmark.add_argument("--compact-pack", type=Path, help="Run the versioned compact deterministic benchmark.")
    benchmark.add_argument("--task-retrieval", action="store_true", help="Measure opt-in task retrieval on the compact pack.")
    benchmark.add_argument("--tasks", type=Path, help="Task pack path relative to the vault root.")
    benchmark.add_argument("--results", type=Path, help="Optional benchmark results path relative to the vault root.")
    benchmark.add_argument(
        "--init-tasks",
        action="store_true",
        help=experimental_help("Create a private benchmark task scaffold."),
    )
    benchmark.add_argument(
        "--init-results",
        action="store_true",
        help=experimental_help("Create a private benchmark result scaffold."),
    )
    benchmark.add_argument("--force", action="store_true", help="Overwrite an existing task or result scaffold.")
    benchmark.add_argument(
        "--scaffold-sources",
        type=int,
        default=5,
        help=experimental_help("Maximum source/mirror pairs for --init-tasks."),
    )
    benchmark.add_argument(
        "--scaffold-curated",
        type=int,
        default=5,
        help=experimental_help("Maximum curated markdown notes for --init-tasks."),
    )
    benchmark.add_argument(
        "--worksheet",
        action="store_true",
        help=experimental_help("Print a private benchmark run worksheet."),
    )
    benchmark.add_argument("--require-generated", action="store_true", help="Require generated mirror paths to exist.")
    benchmark.add_argument("--require-results", action="store_true", help="Require benchmark results for every task/mode pair.")
    benchmark.add_argument(
        "--require-citations",
        action="store_true",
        help="Fail scored benchmark results that do not cite a declared source or generated mirror path.",
    )
    benchmark.add_argument(
        "--require-prompt-safety",
        action="store_true",
        help="Fail benchmark results with missing prompt-safety review or recorded prompt-safety violations.",
    )
    benchmark.add_argument("--json", action="store_true", help="Print machine-readable benchmark JSON.")
    benchmark.set_defaults(func=command_benchmark)
    conversion = sub.add_parser(
        "conversion",
        help=experimental_help("Print a read-only conversion spot-check report."),
    )
    conversion.add_argument("--json", action="store_true", help="Print machine-readable conversion JSON.")
    conversion.add_argument("--guide", action="store_true", help="Append an operator conversion-review checklist.")
    conversion.add_argument("--results", type=Path, help="Validate a metadata-only conversion quality result pack.")
    conversion.add_argument("--init-results", action="store_true", help="Create a metadata-only quality result scaffold.")
    conversion.add_argument("--force", action="store_true", help="Overwrite an existing quality result scaffold.")
    conversion.add_argument(
        "--require-reviewed",
        action="store_true",
        help="Fail unless every source manifest record has a reviewed quality result.",
    )
    conversion.add_argument(
        "--low-risk-per-format",
        type=int,
        default=1,
        help="Include this many low-risk sample records per format in the spot-check list.",
    )
    conversion.set_defaults(func=command_conversion)
    migration = sub.add_parser("migration", help="Report legacy folder/frontmatter migration work.")
    migration_output = migration.add_mutually_exclusive_group()
    migration_output.add_argument("--json", action="store_true", help="Print machine-readable migration JSON.")
    migration_output.add_argument("--worksheet", action="store_true", help="Print a Markdown migration review worksheet.")
    migration_output.add_argument("--runbook", action="store_true", help="Print a Markdown legacy-folder migration runbook.")
    migration.add_argument(
        "--normalize-frontmatter-domains",
        action="store_true",
        help="Preview known legacy frontmatter domain aliases that can be rewritten to canonical domains.",
    )
    migration.add_argument(
        "--write",
        action="store_true",
        help="Apply an explicitly selected migration mode. Never deletes or moves Markdown.",
    )
    migration.add_argument(
        "--apply-markdown-review",
        type=Path,
        help="Apply a reviewed, hash-pinned Markdown classification manifest.",
    )
    migration.add_argument(
        "--backup-dir",
        type=Path,
        help="Backup directory outside the vault, required with --apply-markdown-review.",
    )
    migration.set_defaults(func=command_migration)
    pilot = sub.add_parser("pilot", help=experimental_help("Print a read-only design-partner pilot evidence report."))
    pilot_output = pilot.add_mutually_exclusive_group()
    pilot_output.add_argument("--json", action="store_true", help="Print machine-readable pilot JSON.")
    pilot_output.add_argument(
        "--worksheet",
        action="store_true",
        help="Print a redacted Markdown pilot worksheet summary.",
    )
    pilot.set_defaults(func=command_pilot)
    recovery = sub.add_parser("recovery", help="Print a read-only manifest recovery checklist.")
    recovery_output = recovery.add_mutually_exclusive_group()
    recovery_output.add_argument("--json", action="store_true", help="Print machine-readable recovery JSON.")
    recovery_output.add_argument("--worksheet", action="store_true", help="Print a Markdown recovery review worksheet.")
    recovery_output.add_argument("--runbook", action="store_true", help="Print a Markdown recovery resolution runbook.")
    recovery.set_defaults(func=command_recovery)
    m365 = sub.add_parser("m365", help=experimental_help("Print a read-only Microsoft 365/Copilot handoff report."))
    m365.add_argument("--json", action="store_true", help="Print machine-readable handoff JSON.")
    m365.set_defaults(func=command_m365)
    review = sub.add_parser("review", help="Record or summarize metadata-only artifact review decisions.")
    review.add_argument("--artifact", type=Path, help="Generated artifact to review, relative to the vault root.")
    review.add_argument("--status", choices=["approved", "blocked", "deferred", "needs-work"], help="Review decision to record.")
    review.add_argument("--reviewer", help="Reviewer name or role for a recorded decision.")
    review.add_argument("--note", default="", help="Short metadata-only review note.")
    review.add_argument("--kind", help="Override artifact kind after path safety checks.")
    review.add_argument("--json", action="store_true", help="Print machine-readable review ledger output.")
    review.add_argument("--check", action="store_true", help="Fail unless every latest review is approved and current.")
    review.set_defaults(func=command_review)
    catalog = sub.add_parser("catalog", help="Generate a documentation catalog and local explorer.")
    catalog.add_argument("--json", action="store_true", help="Print machine-readable catalog JSON.")
    catalog.add_argument("--html", action="store_true", help="Write or print an HTML catalog instead of Markdown.")
    catalog.add_argument(
        "--include-content",
        action="store_true",
        help=(
            "Embed bounded Markdown bodies in the HTML explorer for local review. "
            "The resulting file may contain sensitive workspace content."
        ),
    )
    catalog.add_argument("--stdout", action="store_true", help="Print catalog output instead of writing a file.")
    catalog.add_argument("--check", action="store_true", help="Fail if the catalog output is missing or stale.")
    catalog.add_argument(
        "--output",
        type=Path,
        default=Path("CATALOG.md"),
        help="Catalog path relative to the vault root. Defaults to CATALOG.html when --html is used.",
    )
    catalog.add_argument(
        "--max-items",
        type=int,
        default=500,
        help="Maximum source/repo records to list per catalog section; use 0 for no limit.",
    )
    catalog.set_defaults(func=command_catalog)
    sandbox = sub.add_parser("sandbox", help=experimental_help("Print a read-only copied-vault sandbox readiness report."))
    sandbox.add_argument(
        "--source-root",
        type=Path,
        help="Original source collection root. Used only to verify the pilot vault is a separate copy.",
    )
    sandbox.add_argument("--json", action="store_true", help="Print machine-readable sandbox JSON.")
    sandbox.set_defaults(func=command_sandbox)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
