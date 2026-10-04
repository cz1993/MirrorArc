# Optional PageIndex runtime recipe

This is a local compatibility patch, **not an upstream PageIndex release**. It is separate from
MirrorArc's core dependencies. Installation is manual; MirrorArc does not download, patch or
install packages on the user's behalf. See the repository's `docs/PAGEINDEX.md` for the commands.

## Pinned inputs

- Upstream: <https://github.com/VectifyAI/PageIndex>, commit
  `6d23caf416858f2ca136840305d1f479a86f6ef7` (reports `0.2.10`).
- Local distribution: `pageindex==0.2.10+mirrorarc.1`.
- Text/object parser: `pypdf==6.19.0`; PDFium binding: `pypdfium2==5.13.0`.
- Build backend: `poetry-core==2.5.0`, included in the dependency lock.
- Patch SHA-256: `a1b5243921841ca60e518421d94c71964f85cce1422745834131e116848104f7`.
- Dependency-lock SHA-256: `8a9040f9e595ef49eddd3e6c98dcc6532bd45e64c62140b055811d5ef125fc01`.

`pageindex-pypdf.patch` replaces all PyPDF2 imports and the dependency, updates corresponding
upstream test imports, and gives the distribution a distinct local version. The classic helper's
legacy `pdf_parser="PyPDF2"` argument remains an alias for pypdf; it does not load PyPDF2.
No search, reasoning, storage, network or model implementation is replaced by this patch.
Upstream code and its license stay in the separate checkout, not in the user's vault.

The original dependency has no patched PyPDF2 release for
[CVE-2023-36464](https://github.com/py-pdf/pypdf/security/advisories/GHSA-4vvm-4w3v-6mr8).
MirrorArc rejects unpatched `0.2.10`, unexpected parser versions and environments containing
PyPDF2. Reindex after changing the parser contract; historical frozen packs are not rewritten.

## Lock generation and validation

`requirements-py311.txt` was generated on October 3, 2026 with uv 0.12.1 from the patched
upstream `pyproject.toml` and `build-requirements.in`:

```bash
uv pip compile /path/to/patched-PageIndex/pyproject.toml build-requirements.in \
  --python-version 3.11 --universal --generate-hashes --no-header --no-annotate \
  --output-file requirements-py311.txt
```

The universal resolution is not cross-platform runtime proof. The verified installation uses
CPython 3.11.15 on macOS arm64. Linux still requires execution checks. The lock excludes test
tools and PageIndex itself: install its dependencies with hash enforcement, then build the
exact patched source using `--no-deps --no-build-isolation`. Do not resolve new dependencies
silently or install this into an existing environment containing the old parser.

321 focused upstream compatibility tests passed after migration. The full upstream suite with
loopback permitted passed 721 tests, with 100 optional tests skipped; those skips are not proof
of the optional integrations. A synthetic end-of-file comment regression completes without a
hang. These checks and a published-dependency audit do not certify arbitrary PDFs, native code,
the local source patch, model reasoning or enterprise readiness. Re-audit the final environment
before shipment; a version lock is not a permanent security clearance.

## Upstream license for patch context

MIT License

Copyright (c) 2025 Vectify AI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
