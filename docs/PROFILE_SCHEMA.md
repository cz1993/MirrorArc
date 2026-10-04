# MirrorArc Profile Schema

Profiles are versioned behavior contracts. They define source/domain scope, artifact vocabulary,
allowed Markdown categories, relationship types, L2 lenses, review/persistence rules, context
budgets, folders, templates, and benchmark hooks. Runtime code reads this contract instead of
hard-coding an industry taxonomy or encouraging one note per concept.

The current structural schema remains `schema_version: 1`; the knowledge-projection contract is
`profile_version: 0.2.0`. New top-level behavior fields are optional to keep technical-alpha 0.1
profiles readable during migration, but every packaged 0.2 profile declares them explicitly.

## Contract file and commands

Each vault stores its active profile at `_meta/profile.yml`. The default `data-product` profile is
canonical under `template/_meta/profile.yml`; other packaged profiles live under
`src/mirrorarc/builtin_profiles/`.

```bash
mirrorarc profile list
mirrorarc profile show data-product
mirrorarc init --profile data-product <vault>
mirrorarc --root <vault> profile validate
mirrorarc --root <vault> profile diff 0.2.0
mirrorarc --root <vault> profile migrate --plan
mirrorarc --root <vault> profile migrate --write
```

## Core fields

The existing required fields remain:

- `schema_version`, `id`, `name`, `profile_version`, and optional `description`;
- `domains`: canonical folder and purpose by domain ID;
- `note_types`: compatibility/frontmatter vocabulary, including `machine_owned`,
  `legacy_derivative`, and `markdown_category` roles;
- `statuses`: lifecycle/review vocabulary with optional `attention` and `inactive` roles;
- `required_properties` and `optional_properties`;
- `folder_plan`, `templates`, `views`, `skills`, and `benchmark_tasks`;
- `policy_defaults`: mirror/repository and universal safety defaults.

`policy_defaults.native_source_mode` is `direct` by default, so natively readable Markdown and
plain text are registered without a redundant copy. Profiles may instead declare
`isolated_projection` or `immutable_projection` when isolation or snapshot policy requires one.

Domain folders remain unique, non-overlapping, safe vault-relative POSIX paths. Template, view,
skill, and benchmark paths cannot escape the vault or overlap generated mirror output.

## Markdown categories

`markdown_categories` declares the durable artifact policy. Packaged profiles use:

```yaml
markdown_categories:
  index: {persistence: manual}
  authoritative_markdown_source: {persistence: authoritative}
  l1_projection: {persistence: rebuildable}
  l2_generated_view: {persistence: ephemeral}
  l2_reviewed_view: {persistence: governed}
  operational_control: {persistence: required}
```

`legacy_curated_derivative` and `unknown` are migration classifications, not target categories.
`INDEX.md` is the manual guide exception. Native Markdown/plain text may be registered directly as
`authoritative_markdown_source`; opaque sources normally receive one `l1_projection` identity.

Existing note types may remain with `legacy_derivative: true` so an old vault can be inventoried
without treating those types as a fresh-authoring recommendation.

## Relationship vocabulary

`relationship_types` declares deterministic and semantic types plus their review requirement:

```yaml
relationship_types:
  MIRRORS: {deterministic: true, review_required: false}
  DERIVED_FROM: {deterministic: true, review_required: false}
  IN_DOMAIN: {deterministic: true, review_required: false}
  HAS_LIFECYCLE: {deterministic: true, review_required: false}
  IN_PROFILE: {deterministic: true, review_required: false}
  DEPENDS_ON: {deterministic: true, review_required: false}
  REVIEW_DEPENDS_ON: {deterministic: true, review_required: false}
  IN_CONTEXT: {deterministic: true, review_required: false}
  MENTIONS: {deterministic: false, review_required: true}
  SAME_ENTITY: {deterministic: false, review_required: true}
  SUPPORTS: {deterministic: false, review_required: true}
  CONTRADICTS: {deterministic: false, review_required: true}
  SUPERSEDES: {deterministic: false, review_required: true}
  GOVERNS: {deterministic: false, review_required: true}
  INVALIDATES: {deterministic: true, review_required: false}
```

Runtime normalization stores canonical uppercase types. An accepted semantic relation requires
evidence and an admitted review/policy state; model output starts proposed.

`mirrorarc relationships refresh` deterministically rebuilds the current structural graph in the
existing local state database. `status` and `export` expose hashes, bounded anchors, method/version,
confidence, state, and review history without copying source bodies. `propose` and `review` keep
semantic admission explicit.

## Knowledge lenses

`knowledge_lenses` maps a lens ID to:

- `purpose` and `audience`;
- `source_query` and permitted `relationship_types`;
- ordered `output_sections`;
- `max_tokens`;
- `persistence` (`ephemeral`, `cache`, `pinned`, or `reviewed`);
- `citation_required`.

A lens is many sources to one purpose-specific view. Profiles must not generate one view per source
by default. Persistence never implies authority, and automatic promotion is forbidden.

`mirrorarc view render <lens>` first uses the deterministic renderer and writes only a local cache
artifact. The output identity includes the lens definition and dependency hashes, so unchanged
rendering is idempotent while changed evidence creates a distinct candidate. `view pin` and
`view review` are explicit persistence transitions; reviewed output is preserved when stale.
`view promote` requires a named reviewer, a reason, a new in-vault target, and writes promotion
provenance. A profile with `automatic_promotion: true` is invalid.

## Review and context policy

`review_policy` declares:

```yaml
review_policy:
  semantic_proposals_require_review: true
  preserve_reviewed_views: true
  automatic_promotion: false
```

`context_defaults` declares export ceilings and allowed modes:

```yaml
context_defaults:
  max_tokens: 4000
  max_files: 20
  max_excerpt_chars: 6000
  allowed_modes: [metadata, dynamic, frozen]
```

`max_tokens` is a compatibility estimate, not a strict tokenizer ceiling. Frozen exports use
`max_tokens * 4` as a hard UTF-8 serialized JSON byte ceiling, including instructions, metadata,
citations, omissions and whitespace (`utf8-json-bytes-v1`). Accounting reports exact bytes and
`ceil(bytes/4)` estimated tokens. Overhead-only overflow fails rather than writing invalid JSON.
Per-excerpt characters are Unicode codepoints; code truncation retains complete lines only.
Current profile allowed modes are checked before provider, cache, or body access, including saved
definitions after policy changes.

Metadata mode copies no bodies. Dynamic definitions resolve current eligible evidence. Frozen
packs record bounded content or resolvable references plus hashes, citations, omissions, warnings,
and sensitivity. The context ceilings are validated as positive integers, and `allowed_modes`
accepts only `metadata`, `dynamic`, and `frozen`.

```bash
mirrorarc --root <vault> context build --lens orientation --mode metadata
mirrorarc --root <vault> context build --lens orientation --mode dynamic
mirrorarc --root <vault> context resolve <definition-id>
mirrorarc --root <vault> context freeze --definition <definition-id>
mirrorarc --root <vault> context status <context-id>
```

Metadata output is a selection manifest, not a content pack. A dynamic definition stores purpose,
selection rules, budgets, freshness policy, permitted artifact types, and sensitivity policy; each
resolve recomputes membership from current governed state. A frozen pack is a byte-stable JSON
execution envelope with bounded excerpts, source/projection hashes, current relationship evidence,
view versions where applicable, citations, omissions, warnings, and effective sensitivity. Its
status may report newer versions, but refresh never mutates the frozen file.
Effective budget and export-method changes participate in the frozen identity. Publication is
exclusive: an existing identity with different bytes is an integrity error, never an overwrite.
Surviving frozen files retain their creation time when derived database records are rebuilt.

The `software-project` profile can also use optional code-evidence contexts. Repository selection
still comes from `tools/repos.yml`; no provider field or second repository connector is added to the
profile schema. `code analyze --context dynamic|frozen` reuses the same `context_defaults` budgets,
citations, omission reporting, sensitivity boundary, and untrusted-content rules.

## Policy defaults

Current mirror settings remain:

- `mirror_mode`, `mirror_root`, `mirror_status`;
- `repo_notes_dir`, `repo_stub_status`;
- `context_aliases` for profile-specific compatibility;
- `original_sources_authoritative: true`;
- `real_data_in_repo: false`.

These universal booleans cannot be weakened. A profile must not declare an automatic-promotion,
public-body export, vector-index, or parallel lifecycle authority default.

## Runtime and migration semantics

Explicit validation rejects unknown fields, unsafe paths, invalid vocabulary, overlapping folders,
duplicate entries, and policy contradictions. Tolerant runtime readers may apply legacy defaults to
a missing 0.2 behavior field, but `profile diff` and migration report that drift.

`profile migrate --plan` is read-only. Write mode may add missing package-owned files/directories
but never overwrite existing source content, generated projections, reviewed views, or annotation
sidecars. Markdown classification and disposition use `mirrorarc migration`; profile migration and
content migration remain separate gates.

## Packaged profiles

The packaged profiles are `data-product`, `business-operations`, `research-learning`,
`software-project`, and `blank`. They share authority, L1 cardinality, relationship evidence,
many-to-few L2, context, review, and no-data rules while keeping their own domain and source
vocabulary.

## Opt-in task query

`context build --lens orientation --query "your task"` saves the query inside the existing
selection definition; `context freeze --lens orientation --query "your task"` uses it directly.
Explicit selections remain the default. Saved queries and relationship types survive resolution
and recovery. Query retrieval admits only hash-verified current authoritative text or L1, uses
FTS5 `unicode61` with BM25 (heading weight 4, body weight 1), deterministic ties and source-ID
deduplication, then optionally expands one accepted-current relationship hop. Limits: 500
candidates, 256 KiB per indexed file, 8 MiB total indexed text, 10,000 chunks and the existing
profile file/export ceilings. Unsupported FTS5 runtimes give an explicit error and can use lens
selection without a query. The index is disposable; it cannot admit a proposed/rejected edge.
Retrieval diagnostics in exported context contain exclusion counts and at most five examples.
`exclusions_omitted` labels the remaining detail; `details_path` and `details_hash` identify the
full local metadata report under `.mirrorarc/cache/context/retrieval/`. This report is not required
to read the included evidence offline and may be regenerated after cache loss.
