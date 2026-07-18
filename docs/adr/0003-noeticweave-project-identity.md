# ADR 0003: NoeticWeave Project Identity

**Status:** Accepted
**Date:** 2026-07-18
**Owner:** cz1993
**Release mapping:** V1-C9 packaging, upgrade, documentation, and product identity

## Context

The original name, Vaultwright, overemphasized the storage container. The product has converged on
a broader and more specific function: it compiles changing source collections into governed,
profile-driven knowledge workspaces through deterministic mirrors, provenance, lifecycle state,
human review, anti-proliferation rules, and linking-first retrieval.

The preferred replacement was **NoeticLens**. “Noetic” fits knowledge and understanding, while
“lens” suggests inspectability. A live exact-name screen on 2026-07-18 found that the name was
already in active use:

- [`noeticlens.com`](https://noeticlens.com/) identifies Noetic Lens as StoneKey's photography and
  visual-media arm.
- [`github.com/NoeticLens`](https://github.com/NoeticLens) is an existing organization account.

The exact `.com` and GitHub identity collision creates avoidable brand, discovery, repository-slug,
and trademark risk even though the existing use is in a different product category. NoeticLens is
therefore rejected.

An exact-name screen for **NoeticWeave** found no competing product and no claimed GitHub
organization/repository, PyPI distribution, npm package, or `.com` registration at the time of the
decision. This is preliminary screening, not legal clearance.

## Decision

Rename the project to **NoeticWeave**.

- **Noetic** means relating to knowledge, understanding, or intellectual activity.
- **Weave** describes the product's linking-first assembly of sources, mirrors, provenance,
  lifecycle evidence, and curated knowledge into a coherent workspace.
- The product descriptor remains: **Compile changing source collections into governed knowledge
  workspaces.**

Canonical technical identifiers are:

| Surface | Canonical identity |
| --- | --- |
| Product | `NoeticWeave` |
| Repository target | `cz1993/noeticweave` |
| Python distribution | `noeticweave` |
| Python namespace | `noeticweave` |
| Console command | `noeticweave` |
| Source package | `src/noeticweave/` |
| Local derived state | `.noeticweave/state.sqlite` |
| Benchmark mode | `noeticweave_markdown` |
| Development variables | `NOETICWEAVE_REPO`, `NOETICWEAVE_PYTHON` |

## Transition Boundary

The project is a technical alpha with no completed external pilot, so this is the lowest-cost point
for a comprehensive rename. New artifacts must use NoeticWeave exclusively. Narrow compatibility
remains for existing local alpha work:

- the previous console command delegates to `noeticweave.cli`;
- the previous Python namespace resolves submodules from the canonical NoeticWeave package;
- the previous development environment variables remain fallback inputs;
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
