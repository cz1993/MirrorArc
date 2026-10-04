# SPDX-License-Identifier: AGPL-3.0-or-later
"""Profile contract loading and validation."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


PROFILE_SCHEMA_VERSION = 1
PROFILE_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PROFILE_KEY_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$")
REQUIRED_FIELDS = {
    "schema_version",
    "id",
    "name",
    "profile_version",
    "domains",
    "note_types",
    "statuses",
    "required_properties",
    "optional_properties",
    "folder_plan",
    "templates",
    "views",
    "skills",
    "benchmark_tasks",
    "policy_defaults",
}
OPTIONAL_FIELDS = {
    "context_defaults",
    "description",
    "knowledge_lenses",
    "markdown_categories",
    "relationship_types",
    "review_policy",
}
LIST_FIELDS = {
    "required_properties",
    "optional_properties",
    "folder_plan",
    "templates",
    "views",
    "skills",
    "benchmark_tasks",
}
MAPPING_FIELDS = {"domains", "note_types", "statuses", "policy_defaults"}
FORBIDDEN_PROFILE_PATH_PARTS = {".git", ".githooks", ".github", "node_modules"}
DOMAIN_DEFINITION_FIELDS = {"folder", "purpose"}
NOTE_TYPE_DEFINITION_FIELDS = {"purpose", "machine_owned", "legacy_derivative", "markdown_category"}
NOTE_TYPE_BOOLEAN_FIELDS = {"machine_owned", "legacy_derivative"}
STATUS_DEFINITION_FIELDS = {"purpose", "attention", "inactive"}
STATUS_BOOLEAN_FIELDS = {"attention", "inactive"}
FOLDER_PLAN_FIELDS = {"path", "domain"}
POLICY_STATUS_DEFAULT_FIELDS = {"mirror_status", "repo_stub_status"}
POLICY_BOOLEAN_DEFAULT_FIELDS = {"original_sources_authoritative", "real_data_in_repo"}
POLICY_REQUIRED_TRUE_DEFAULT_FIELDS = {"original_sources_authoritative"}
POLICY_REQUIRED_FALSE_DEFAULT_FIELDS = {"real_data_in_repo"}
POLICY_DEFAULT_FIELDS = {
    "context_aliases",
    "mirror_mode",
    "mirror_root",
    "mirror_status",
    "native_source_mode",
    "original_sources_authoritative",
    "real_data_in_repo",
    "repo_notes_dir",
    "repo_stub_status",
}
MIRROR_MODES = {"dedicated", "sibling"}
NATIVE_SOURCE_MODES = {"direct", "isolated_projection", "immutable_projection"}
MARKDOWN_CATEGORY_KEYS = {
    "index", "authoritative_markdown_source", "l1_projection", "l2_generated_view",
    "l2_reviewed_view", "operational_control",
}
RELATIONSHIP_TYPE_KEYS = {
    "MIRRORS", "DERIVED_FROM", "IN_DOMAIN", "HAS_LIFECYCLE", "IN_PROFILE",
    "DEPENDS_ON", "REVIEW_DEPENDS_ON", "IN_CONTEXT", "MENTIONS", "SAME_ENTITY",
    "SUPPORTS", "CONTRADICTS", "SUPERSEDES", "GOVERNS", "INVALIDATES",
}
LENS_REQUIRED_FIELDS = {
    "purpose", "audience", "source_query", "relationship_types", "output_sections",
    "max_tokens", "persistence", "citation_required",
}
LENS_OPTIONAL_FIELDS = {"refresh", "model_assisted", "max_sources", "citation_style"}
REVIEW_POLICY_FIELDS = {
    "semantic_proposals_require_review", "preserve_reviewed_views", "automatic_promotion",
}
CONTEXT_DEFAULT_FIELDS = {"max_tokens", "max_files", "max_excerpt_chars", "allowed_modes"}
CONTEXT_MODES = {"metadata", "dynamic", "frozen"}
FORBIDDEN_MIRROR_ROOT_PARTS = {
    ".git",
    ".githooks",
    ".github",
    ".obsidian",
    "_archive",
    "_fixtures",
    "_meta",
    "_templates",
    "_tmp",
    "node_modules",
    "tools",
}
FORBIDDEN_REPO_NOTES_DIR_PARTS = {
    ".git",
    ".githooks",
    ".github",
    ".obsidian",
    "_archive",
    "_fixtures",
    "_meta",
    "_mirrors",
    "_templates",
    "_tmp",
    "node_modules",
    "tools",
}
FORBIDDEN_PROFILE_ARTIFACT_PATH_PARTS = {
    ".git",
    ".githooks",
    ".github",
    ".obsidian",
    "_archive",
    "_fixtures",
    "_meta",
    "_mirrors",
    "_tmp",
    "node_modules",
    "tools",
}


class ProfileValidationError(ValueError):
    """Raised when a profile contract is missing required structure."""


@dataclass(frozen=True)
class ProfileContract:
    schema_version: int
    id: str
    name: str
    profile_version: str
    domains: dict[str, Any]
    note_types: dict[str, Any]
    statuses: dict[str, Any]
    required_properties: list[Any]
    optional_properties: list[Any]
    folder_plan: list[Any]
    templates: list[Any]
    views: list[Any]
    skills: list[Any]
    benchmark_tasks: list[Any]
    policy_defaults: dict[str, Any]
    description: str = ""
    markdown_categories: dict[str, Any] = field(default_factory=dict)
    relationship_types: dict[str, Any] = field(default_factory=dict)
    knowledge_lenses: dict[str, Any] = field(default_factory=dict)
    review_policy: dict[str, Any] = field(default_factory=dict)
    context_defaults: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "ProfileContract":
        validate_profile_mapping(data)
        return cls(
            schema_version=int(data["schema_version"]),
            id=str(data["id"]),
            name=str(data["name"]),
            profile_version=str(data["profile_version"]),
            domains=dict(data["domains"]),
            note_types=dict(data["note_types"]),
            statuses=dict(data["statuses"]),
            required_properties=list(data["required_properties"]),
            optional_properties=list(data["optional_properties"]),
            folder_plan=list(data["folder_plan"]),
            templates=list(data["templates"]),
            views=list(data["views"]),
            skills=list(data["skills"]),
            benchmark_tasks=list(data["benchmark_tasks"]),
            policy_defaults=dict(data["policy_defaults"]),
            description=str(data.get("description", "")),
            markdown_categories=dict(data.get("markdown_categories", {})),
            relationship_types=dict(data.get("relationship_types", {})),
            knowledge_lenses=dict(data.get("knowledge_lenses", {})),
            review_policy=dict(data.get("review_policy", {})),
            context_defaults=dict(data.get("context_defaults", {})),
        )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "profile_version": self.profile_version,
            "schema_version": self.schema_version,
            "domains": len(self.domains),
            "note_types": len(self.note_types),
            "statuses": len(self.statuses),
            "templates": len(self.templates),
            "views": len(self.views),
            "relationship_types": len(self.relationship_types),
            "knowledge_lenses": len(self.knowledge_lenses),
        }


def validate_string(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ProfileValidationError(f"{field} must be a non-empty string")


def validate_profile_key(value: Any, field: str) -> str:
    validate_string(value, field)
    text = str(value).strip()
    if not PROFILE_KEY_RE.fullmatch(text):
        raise ProfileValidationError(f"{field} must be lowercase kebab-case")
    return text


def validate_known_mapping_fields(data: dict[str, Any], allowed: set[str], field: str) -> None:
    unknown = sorted(set(data) - allowed)
    if unknown:
        raise ProfileValidationError(f"{field} has unknown fields: {', '.join(unknown)}")


def validate_frontmatter_key(value: Any, field: str) -> str:
    validate_string(value, field)
    text = str(value).strip()
    if not FRONTMATTER_KEY_RE.fullmatch(text):
        raise ProfileValidationError(f"{field} must be a lowercase frontmatter key")
    return text


def validate_knowledge_projection_fields(data: dict[str, Any]) -> None:
    categories = data.get("markdown_categories", {})
    for category, definition in categories.items():
        if category not in MARKDOWN_CATEGORY_KEYS:
            raise ProfileValidationError(f"unsupported markdown_categories key: {category}")
        if not isinstance(definition, dict) or not isinstance(definition.get("persistence"), str):
            raise ProfileValidationError(f"markdown_categories.{category}.persistence is required")

    relationship_types = data.get("relationship_types", {})
    for relationship_type, definition in relationship_types.items():
        if relationship_type not in RELATIONSHIP_TYPE_KEYS:
            raise ProfileValidationError(f"unsupported relationship_types key: {relationship_type}")
        if not isinstance(definition, dict):
            raise ProfileValidationError(f"relationship_types.{relationship_type} must be a mapping")
        for field_name in ("deterministic", "review_required"):
            if not isinstance(definition.get(field_name), bool):
                raise ProfileValidationError(f"relationship_types.{relationship_type}.{field_name} must be true or false")

    lenses = data.get("knowledge_lenses", {})
    for lens_id, definition in lenses.items():
        validate_profile_key(lens_id, "knowledge_lenses key")
        if not isinstance(definition, dict):
            raise ProfileValidationError(f"knowledge_lenses.{lens_id} must be a mapping")
        unknown = sorted(set(definition) - LENS_REQUIRED_FIELDS - LENS_OPTIONAL_FIELDS)
        missing = sorted(LENS_REQUIRED_FIELDS - set(definition))
        if unknown:
            raise ProfileValidationError(f"knowledge_lenses.{lens_id} has unknown fields: {', '.join(unknown)}")
        if missing:
            raise ProfileValidationError(f"knowledge_lenses.{lens_id} missing fields: {', '.join(missing)}")
        for field_name in ("purpose", "audience", "persistence"):
            validate_string(definition.get(field_name), f"knowledge_lenses.{lens_id}.{field_name}")
        if definition["persistence"] == "reviewed":
            raise ProfileValidationError(f"knowledge_lenses.{lens_id} cannot automatically persist as reviewed")
        if not isinstance(definition.get("source_query"), dict):
            raise ProfileValidationError(f"knowledge_lenses.{lens_id}.source_query must be a mapping")
        priority_paths = definition["source_query"].get("priority_paths", [])
        if not isinstance(priority_paths, list) or any(not isinstance(item, str) or not item.strip() for item in priority_paths):
            raise ProfileValidationError(
                f"knowledge_lenses.{lens_id}.source_query.priority_paths must be a list of non-empty strings"
            )
        for field_name in ("relationship_types", "output_sections"):
            value = definition.get(field_name)
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                raise ProfileValidationError(f"knowledge_lenses.{lens_id}.{field_name} must be a list of strings")
        invalid_types = sorted(set(definition["relationship_types"]) - set(relationship_types))
        if invalid_types:
            raise ProfileValidationError(
                f"knowledge_lenses.{lens_id}.relationship_types are undeclared: {', '.join(invalid_types)}"
            )
        if not isinstance(definition.get("max_tokens"), int) or definition["max_tokens"] < 100:
            raise ProfileValidationError(f"knowledge_lenses.{lens_id}.max_tokens must be an integer >= 100")
        if not isinstance(definition.get("citation_required"), bool):
            raise ProfileValidationError(f"knowledge_lenses.{lens_id}.citation_required must be true or false")

    review_policy = data.get("review_policy", {})
    unknown_policy = sorted(set(review_policy) - REVIEW_POLICY_FIELDS)
    if unknown_policy:
        raise ProfileValidationError(f"review_policy has unknown fields: {', '.join(unknown_policy)}")
    for field_name, value in review_policy.items():
        if not isinstance(value, bool):
            raise ProfileValidationError(f"review_policy.{field_name} must be true or false")
    if review_policy.get("automatic_promotion") is True:
        raise ProfileValidationError("review_policy.automatic_promotion must be false")

    context_defaults = data.get("context_defaults", {})
    if not isinstance(context_defaults, dict):
        raise ProfileValidationError("context_defaults must be a mapping")
    unknown_context = sorted(set(context_defaults) - CONTEXT_DEFAULT_FIELDS)
    if unknown_context:
        raise ProfileValidationError(f"context_defaults has unknown fields: {', '.join(unknown_context)}")
    if context_defaults:
        missing_context = sorted(CONTEXT_DEFAULT_FIELDS - set(context_defaults))
        if missing_context:
            raise ProfileValidationError(f"context_defaults missing fields: {', '.join(missing_context)}")
        for field_name in ("max_tokens", "max_files", "max_excerpt_chars"):
            if not isinstance(context_defaults.get(field_name), int) or context_defaults[field_name] <= 0:
                raise ProfileValidationError(f"context_defaults.{field_name} must be a positive integer")
        modes = context_defaults.get("allowed_modes")
        if not isinstance(modes, list) or not modes or any(not isinstance(mode, str) for mode in modes):
            raise ProfileValidationError("context_defaults.allowed_modes must be a non-empty list of strings")
        invalid_modes = sorted(set(modes) - CONTEXT_MODES)
        if invalid_modes:
            raise ProfileValidationError(
                f"context_defaults.allowed_modes are unsupported: {', '.join(invalid_modes)}"
            )


def validate_profile_path(value: Any, field: str) -> PurePosixPath:
    validate_string(value, field)
    text = str(value).strip()
    if "\\" in text:
        raise ProfileValidationError(f"{field} must use POSIX-style '/' separators")
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts or not path.parts or path.as_posix() == ".":
        raise ProfileValidationError(f"{field} must stay inside the vault")
    if any(part.startswith(".") or part in FORBIDDEN_PROFILE_PATH_PARTS for part in path.parts):
        raise ProfileValidationError(f"{field} contains a reserved path component")
    return path


def validate_mirror_root(value: Any, field: str) -> PurePosixPath:
    path = validate_profile_path(value, field)
    if any(part.startswith(".") or part in FORBIDDEN_MIRROR_ROOT_PARTS for part in path.parts):
        raise ProfileValidationError(f"{field} contains a reserved path component")
    return path


def validate_repo_notes_dir(
    value: Any,
    field: str,
    domain_folders: dict[str, PurePosixPath],
    mirror_root: PurePosixPath | None,
) -> PurePosixPath:
    path = validate_profile_path(value, field)
    if any(part.startswith(".") or part in FORBIDDEN_REPO_NOTES_DIR_PARTS for part in path.parts):
        raise ProfileValidationError(f"{field} contains a reserved path component")
    if not any(path_is_under(path, folder) for folder in domain_folders.values()):
        raise ProfileValidationError(f"{field} must be inside a declared domain folder")
    if mirror_root and (path_is_under(path, mirror_root) or path_is_under(mirror_root, path)):
        raise ProfileValidationError(f"{field} must not overlap policy_defaults.mirror_root")
    return path


def validate_profile_artifact_path(value: Any, field: str) -> PurePosixPath:
    path = validate_profile_path(value, field)
    if any(part.startswith(".") or part in FORBIDDEN_PROFILE_ARTIFACT_PATH_PARTS for part in path.parts):
        raise ProfileValidationError(f"{field} contains a reserved path component")
    return path


def validate_profile_artifact_list(values: list[Any], field: str) -> None:
    seen_paths: set[str] = set()
    for value in values:
        path = validate_profile_artifact_path(value, f"{field} entry")
        path_text = path.as_posix()
        if path_text in seen_paths:
            raise ProfileValidationError(f"{field} entries must not contain duplicates")
        seen_paths.add(path_text)


def validate_paths_do_not_overlap_mirror_root(data: dict[str, Any], mirror_root: PurePosixPath | None) -> None:
    if mirror_root is None:
        return
    for field in ("templates", "views", "skills", "benchmark_tasks"):
        for value in data[field]:
            path = validate_profile_path(value, f"{field} entry")
            if path_is_under(path, mirror_root):
                raise ProfileValidationError(
                    f"{field} entry must not overlap policy_defaults.mirror_root"
                )


def path_is_under(path: PurePosixPath, directory: PurePosixPath) -> bool:
    return path == directory or (
        len(path.parts) > len(directory.parts)
        and path.parts[: len(directory.parts)] == directory.parts
    )


def validate_folder_plan(folder_plan: Any, domain_folders: dict[str, PurePosixPath]) -> None:
    if not folder_plan:
        raise ProfileValidationError("folder_plan must contain at least one starter folder")

    seen_paths: set[str] = set()
    for index, entry in enumerate(folder_plan):
        field = f"folder_plan[{index}]"
        if not isinstance(entry, dict):
            raise ProfileValidationError(f"{field} must be a mapping")
        validate_known_mapping_fields(entry, FOLDER_PLAN_FIELDS, field)
        path = validate_profile_path(entry.get("path"), f"{field}.path")
        domain = entry.get("domain")
        domain_name = validate_profile_key(domain, f"{field}.domain")
        if domain_name not in domain_folders:
            raise ProfileValidationError(f"{field}.domain must reference a declared domain")
        if not path_is_under(path, domain_folders[domain_name]):
            raise ProfileValidationError(f"{field}.path must be inside domains.{domain_name}.folder")
        path_text = path.as_posix()
        if path_text in seen_paths:
            raise ProfileValidationError(f"{field}.path duplicates another folder_plan path")
        seen_paths.add(path_text)


def validate_domain_folders(domain_folders: dict[str, PurePosixPath]) -> None:
    seen_folders: dict[str, str] = {}
    for domain_name, folder in domain_folders.items():
        folder_text = folder.as_posix()
        previous_domain = seen_folders.get(folder_text)
        if previous_domain:
            raise ProfileValidationError(
                f"domains.{domain_name}.folder duplicates domains.{previous_domain}.folder"
            )
        seen_folders[folder_text] = domain_name

    items = list(domain_folders.items())
    for index, (domain_name, folder) in enumerate(items):
        for other_domain, other_folder in items[index + 1 :]:
            if path_is_under(folder, other_folder) or path_is_under(other_folder, folder):
                raise ProfileValidationError(
                    f"domains.{domain_name}.folder must not overlap domains.{other_domain}.folder"
                )


def validate_context_aliases(value: Any, optional_properties: set[str]) -> None:
    if not isinstance(value, dict):
        raise ProfileValidationError("policy_defaults.context_aliases must be a mapping")
    for alias, target in value.items():
        alias_key = validate_frontmatter_key(alias, "policy_defaults.context_aliases key")
        target_key = validate_frontmatter_key(target, f"policy_defaults.context_aliases.{alias_key}")
        if alias_key == target_key:
            raise ProfileValidationError(f"policy_defaults.context_aliases.{alias_key} must not reference itself")
        if alias_key not in optional_properties:
            raise ProfileValidationError(
                f"policy_defaults.context_aliases.{alias_key} must reference optional_properties"
            )
        if target_key not in optional_properties:
            raise ProfileValidationError(
                f"policy_defaults.context_aliases.{alias_key} target must reference optional_properties"
            )


def validate_profile_mapping(data: Any) -> None:
    if not isinstance(data, dict):
        raise ProfileValidationError("profile must be a mapping")

    unknown = sorted(set(data) - REQUIRED_FIELDS - OPTIONAL_FIELDS)
    if unknown:
        raise ProfileValidationError(f"unknown profile fields: {', '.join(unknown)}")

    missing = sorted(REQUIRED_FIELDS - set(data))
    if missing:
        raise ProfileValidationError(f"missing profile fields: {', '.join(missing)}")

    if data.get("schema_version") != PROFILE_SCHEMA_VERSION:
        raise ProfileValidationError(f"schema_version must be {PROFILE_SCHEMA_VERSION}")

    validate_string(data.get("id"), "id")
    if not PROFILE_ID_RE.fullmatch(str(data["id"])):
        raise ProfileValidationError("id must be lowercase kebab-case")

    validate_string(data.get("name"), "name")
    validate_string(data.get("profile_version"), "profile_version")

    for field in MAPPING_FIELDS:
        if not isinstance(data.get(field), dict):
            raise ProfileValidationError(f"{field} must be a mapping")

    for field in (
        "markdown_categories",
        "relationship_types",
        "knowledge_lenses",
        "review_policy",
        "context_defaults",
    ):
        if field in data and not isinstance(data[field], dict):
            raise ProfileValidationError(f"{field} must be a mapping")

    validate_knowledge_projection_fields(data)

    for field in LIST_FIELDS:
        if not isinstance(data.get(field), list):
            raise ProfileValidationError(f"{field} must be a list")

    for field in ("required_properties", "optional_properties", "templates", "views", "skills", "benchmark_tasks"):
        for value in data[field]:
            if not isinstance(value, str):
                raise ProfileValidationError(f"{field} entries must be strings")
    frontmatter_properties: dict[str, set[str]] = {}
    for field in ("required_properties", "optional_properties"):
        seen_properties: set[str] = set()
        for value in data[field]:
            name = validate_frontmatter_key(value, f"{field} entries")
            if name in seen_properties:
                raise ProfileValidationError(f"{field} entries must not contain duplicates")
            seen_properties.add(name)
        frontmatter_properties[field] = seen_properties
    overlapping_properties = sorted(
        frontmatter_properties["required_properties"] & frontmatter_properties["optional_properties"]
    )
    if overlapping_properties:
        raise ProfileValidationError(
            "required_properties and optional_properties must not overlap: "
            + ", ".join(overlapping_properties)
        )
    for field in ("templates", "views", "skills"):
        validate_profile_artifact_list(data[field], field)
    for value in data["benchmark_tasks"]:
        path = validate_profile_path(value, "benchmark_tasks entry")
        if path.suffix not in {".yml", ".yaml"}:
            raise ProfileValidationError("benchmark_tasks entries must be .yml or .yaml files")

    domain_folders: dict[str, PurePosixPath] = {}
    for domain, definition in data["domains"].items():
        domain_name = validate_profile_key(domain, "domain key")
        if not isinstance(definition, dict):
            raise ProfileValidationError(f"domains.{domain} must be a mapping")
        validate_known_mapping_fields(definition, DOMAIN_DEFINITION_FIELDS, f"domains.{domain_name}")
        if "purpose" in definition:
            validate_string(definition["purpose"], f"domains.{domain_name}.purpose")
        domain_folders[domain_name] = validate_profile_path(
            definition.get("folder"),
            f"domains.{domain}.folder",
        )
    validate_domain_folders(domain_folders)

    for note_type, definition in data["note_types"].items():
        note_type_name = validate_profile_key(note_type, "note_types key")
        if not isinstance(definition, dict):
            raise ProfileValidationError(f"note_types.{note_type} must be a mapping")
        validate_known_mapping_fields(definition, NOTE_TYPE_DEFINITION_FIELDS, f"note_types.{note_type_name}")
        if "purpose" in definition:
            validate_string(definition["purpose"], f"note_types.{note_type_name}.purpose")
        for field in NOTE_TYPE_BOOLEAN_FIELDS:
            if field in definition and not isinstance(definition[field], bool):
                raise ProfileValidationError(f"note_types.{note_type_name}.{field} must be true or false")
        if "markdown_category" in definition:
            validate_string(definition["markdown_category"], f"note_types.{note_type_name}.markdown_category")

    for status, definition in data["statuses"].items():
        status_name = validate_profile_key(status, "status key")
        if not isinstance(definition, dict):
            raise ProfileValidationError(f"statuses.{status} must be a mapping")
        validate_known_mapping_fields(definition, STATUS_DEFINITION_FIELDS, f"statuses.{status_name}")
        if "purpose" in definition:
            validate_string(definition["purpose"], f"statuses.{status_name}.purpose")
        for field in STATUS_BOOLEAN_FIELDS:
            if field in definition and not isinstance(definition[field], bool):
                raise ProfileValidationError(f"statuses.{status_name}.{field} must be true or false")

    validate_known_mapping_fields(data["policy_defaults"], POLICY_DEFAULT_FIELDS, "policy_defaults")

    for field in POLICY_STATUS_DEFAULT_FIELDS:
        if field not in data["policy_defaults"]:
            continue
        value = data["policy_defaults"][field]
        validate_string(value, f"policy_defaults.{field}")
        if str(value).strip() not in data["statuses"]:
            raise ProfileValidationError(f"policy_defaults.{field} must reference a declared status")

    for field in POLICY_BOOLEAN_DEFAULT_FIELDS:
        if field not in data["policy_defaults"]:
            continue
        value = data["policy_defaults"][field]
        if not isinstance(value, bool):
            raise ProfileValidationError(f"policy_defaults.{field} must be true or false")
        if field in POLICY_REQUIRED_TRUE_DEFAULT_FIELDS and value is not True:
            raise ProfileValidationError(f"policy_defaults.{field} must be true")
        if field in POLICY_REQUIRED_FALSE_DEFAULT_FIELDS and value is not False:
            raise ProfileValidationError(f"policy_defaults.{field} must be false")

    if "context_aliases" in data["policy_defaults"]:
        validate_context_aliases(data["policy_defaults"]["context_aliases"], frontmatter_properties["optional_properties"])

    if "mirror_mode" in data["policy_defaults"]:
        mirror_mode = data["policy_defaults"]["mirror_mode"]
        validate_string(mirror_mode, "policy_defaults.mirror_mode")
        if str(mirror_mode).strip() not in MIRROR_MODES:
            raise ProfileValidationError("policy_defaults.mirror_mode must be one of: dedicated, sibling")

    if "native_source_mode" in data["policy_defaults"]:
        native_source_mode = data["policy_defaults"]["native_source_mode"]
        validate_string(native_source_mode, "policy_defaults.native_source_mode")
        if str(native_source_mode).strip() not in NATIVE_SOURCE_MODES:
            raise ProfileValidationError(
                "policy_defaults.native_source_mode must be one of: direct, isolated_projection, immutable_projection"
            )

    mirror_root: PurePosixPath | None = None
    if "mirror_root" in data["policy_defaults"]:
        mirror_root = validate_mirror_root(data["policy_defaults"]["mirror_root"], "policy_defaults.mirror_root")

    if "repo_notes_dir" in data["policy_defaults"]:
        validate_repo_notes_dir(
            data["policy_defaults"]["repo_notes_dir"],
            "policy_defaults.repo_notes_dir",
            domain_folders,
            mirror_root,
        )

    validate_paths_do_not_overlap_mirror_root(data, mirror_root)
    validate_folder_plan(data["folder_plan"], domain_folders)


def load_profile(path: Path) -> ProfileContract:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ProfileValidationError(f"{path} is not valid YAML: {exc}") from exc
    except OSError as exc:
        raise ProfileValidationError(f"cannot read profile: {path}: {exc}") from exc
    return ProfileContract.from_mapping(raw)


def profile_folder_paths(profile: ProfileContract) -> list[Path]:
    paths: list[Path] = []
    seen: set[str] = set()
    for entry in profile.folder_plan:
        if not isinstance(entry, dict):
            continue
        value = entry.get("path")
        if not isinstance(value, str) or not value.strip():
            continue
        rel = PurePosixPath(value.strip()).as_posix()
        if rel in seen:
            continue
        seen.add(rel)
        paths.append(Path(rel))
    return paths
