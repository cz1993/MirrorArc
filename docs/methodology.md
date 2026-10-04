# Methodology

MirrorArc is a source-preserving operating discipline encoded in profiles, manifests, ledgers,
views, context definitions, lint rules, and recovery procedures.

## 1. Authority and projection layers

- **L0 authoritative records** are original files, repositories, exports, and deliberately authored
  records. Agents read them but do not mutate them through derived output.
- **L1 specular projections** make opaque sources inspectable as Markdown. One active opaque source
  identity normally has one active projection identity. Generated bodies are machine-owned.
- **Relationships** are ledger records, not notes. They carry type, evidence, hashes, method,
  confidence where applicable, review state, and invalidation state.
- **L2 knowledge views** answer a purpose for an audience by synthesizing many sources. They are
  ephemeral by default and persist only through an explicit pin, review, audit, or reproducibility
  policy.
- **Context** is assembled for a task as metadata-only selection, a dynamic definition, or a frozen
  evidence pack. It is never source authority.

`INDEX.md` is the manual guide exception: it explains scope, boundaries, and navigation without
becoming a hand-maintained factual digest.

## 2. Source admission and L1 discipline

1. Verify source boundary, rights, sensitivity, and retention policy.
2. Register stable source identity before deriving output.
3. Project opaque formats through the package-owned mirror engine.
4. Register native Markdown/plain text directly unless policy requires isolation or an immutable
   projection.
5. Preserve conversion warnings; `clean` means the declared converter completed against the
   recorded hash, not that extraction is semantically lossless.
6. Never edit generated bodies. Put deliberate human authority in a declared source record; keep
   legacy mirror annotations in sidecars until migrated.

## 3. Linking-first without document proliferation

Retrieval starts from stable identities, profile metadata, deterministic relationships, and
evidenced semantic relationships. A relationship must resolve to a rule or bounded evidence; an
unexplained edge is only a proposal. A synthesis is a view, not a durable record, unless a person
explicitly promotes it and accepts authority.

Before persisting Markdown, classify why it must exist:

- `index`;
- `authoritative_markdown_source`;
- `l1_projection`;
- `l2_generated_view` or `l2_reviewed_view`;
- `operational_control`.

Anything else is legacy or unexplained and must be inventoried before write-mode migration.

## 4. Refresh and invalidation

Events trigger candidate work; reconciliation establishes completeness. After stable-source checks
and L1 materialization, invalidate only ledger edges, reviews, views, and frozen-context freshness
that depend on the changed identity/hash. Preserve reviewed views as stale, generate replacement
candidates separately, keep dynamic definitions intact, and use full sync plus rebuild as the
recovery proof.

## 5. Human review and promotion

- Deterministic relationships may be accepted automatically by profile policy.
- Semantic model output begins proposed and requires evidence plus policy or review admission.
- Rejection and invalidation remain auditable.
- Pinning persists a derived view definition/output; review governs a version.
- Promotion creates a new authoritative record only after explicit human intent and preserves
  derivation history.

## 6. Agent operating loop

1. **Orient:** read `INDEX.md`, profile policy, current status, and relevant governed views.
2. **Admit/project:** plan source admission and L1 actions before writes.
3. **Connect:** refresh deterministic relations; propose semantics only within configured
   vocabulary and evidence budgets.
4. **Interpret:** render the smallest useful L2 view, citing dependencies.
5. **Assemble:** choose selection, dynamic, or frozen context with explicit budgets/sensitivity.
6. **Verify:** lint, review invalidation/staleness, reconcile, and record machine-readable evidence.

## 7. Governance

Secrets never enter the vault. Private, personal, client, proprietary, or rights-unclear material
does not enter this repository or public output. Content-inclusive portals, semantic associations,
view bodies, and frozen packs inherit the strictest source sensitivity and retention policy.
