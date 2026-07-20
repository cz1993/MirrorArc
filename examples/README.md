# Flagship Example: Ontario Electricity Evidence Workspace

`ontario-electricity-evidence-vault/` is MirrorArc's single, end-to-end example. It is a clean-room
data-product workspace built from public Ontario energy material, independently authored
documentation, and clearly labelled synthetic fixtures. It contains more than 50 meaningful files
across sources, contracts, pipelines, historical analysis, outputs, governance, operations, and a
small local repository fixture.

The example demonstrates:

- OGL Ontario CSV source files with exact attribution and an archive checksum.
- Metadata-only links to IESO reference pages; no IESO page body is copied.
- Word, Excel, and repository source mirroring into traceable Markdown.
- A synthetic local code repository mirrored into `20_sources/repos/`.
- A relationship-rich documentation layer for humans and agents.
- Historical completeness and reconciliation checks with explicit, inspectable rules.

The committed snapshot is historical and educational. It is not a live view of Ontario's grid,
does not emit alerts or forecasts, and is not affiliated with or endorsed by Ontario, the IESO,
or the OEB.

To exercise the example without committing generated state:

```bash
cd examples/ontario-electricity-evidence-vault
python3.11 tools/mirrorarc.py plan
python3.11 tools/mirrorarc.py sync
python3.11 tools/mirrorarc.py status
python3.11 tools/mirrorarc.py lint
```

Generated mirrors, manifests, and audit logs remain ignored. Exact source and licence
classifications are recorded in `DATA_PROVENANCE.md`.
