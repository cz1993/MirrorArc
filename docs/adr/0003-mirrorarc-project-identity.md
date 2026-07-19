# ADR 0003: MirrorArc Project Identity

**Status:** Accepted
**Date:** 2026-07-18
**Owner:** cz1993
**Release mapping:** V1-C9 packaging, upgrade, documentation, and product identity

## Context

The original name, Vaultwright, overemphasized the storage container. The product has converged on
a broader and more specific function: it compiles changing source collections into governed,
profile-driven knowledge workspaces through deterministic mirrors, provenance, lifecycle state,
human review, anti-proliferation rules, and linking-first retrieval.

The replacement needed to be short, easy to say, memorable, and tied to the product's actual
function rather than to a generic knowledge or AI category. **MirrorArc** was selected after a
live exact-name screen found no competing product and no claimed GitHub repository, PyPI
distribution, npm package, or `.com` registration at the time of the decision. This is preliminary
screening, not legal clearance.

## Decision

Rename the project to **MirrorArc**.

- **Mirror** names the deterministic, source-preserving Markdown mirror layer that keeps original
  records authoritative.
- **Arc** describes the connected path from changing sources through provenance, lifecycle state,
  human review, and curated knowledge into an inspectable workspace.
- The product descriptor remains: **Compile changing source collections into governed knowledge
  workspaces.**

Canonical technical identifiers are:

| Surface | Canonical identity |
| --- | --- |
| Product | `MirrorArc` |
| Repository target | `cz1993/MirrorArc` |
| Python distribution | `mirrorarc` |
| Python namespace | `mirrorarc` |
| Console command | `mirrorarc` |
| Source package | `src/mirrorarc/` |
| Local derived state | `.mirrorarc/state.sqlite` |
| Benchmark mode | `mirrorarc_markdown` |
| Development variables | `MIRRORARC_REPO`, `MIRRORARC_PYTHON` |

## Transition Boundary

The project is a technical alpha with no completed external pilot, so this is the lowest-cost point
for a comprehensive rename. New artifacts must use MirrorArc exclusively. Narrow compatibility
remains for existing local alpha work:

- the `vaultwright` console command delegates to `mirrorarc.cli`;
- the `vaultwright` Python namespace resolves submodules from the canonical MirrorArc package;
- `VAULTWRIGHT_REPO` and `VAULTWRIGHT_PYTHON` remain fallback development inputs;
- `.vaultwright/state.sqlite` remains readable in place when the new state path does not exist;
- private benchmark packs using `vaultwright_markdown` remain valid with a migration warning.

Compatibility exists to prevent local state loss and abrupt pilot-tool failure. It is not a second
product identity and must not appear in new quickstarts, generated artifacts, examples, or public
claims.

## Consequences

- Canonical docs, package metadata, code imports, templates, examples, workflows, and release
  artifacts move together so the project does not ship a split identity.
- Historical planning filenames are renamed so canonical links do not depend on the retired brand;
  repository history still preserves the old names.
- Existing local checkouts may keep their directory name until recloned or manually moved; Git does
  not require the working-copy folder to match the repository slug.
- The public repository should be renamed only after this branch passes all release gates. GitHub
  redirects preserve old URLs, but local remotes should then be updated explicitly.
- Counsel-led trademark clearance remains required before launch, registration, outside
  contributions, or commercial reliance on the mark.
