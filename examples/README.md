# Flagship Example: Ontario Grid Evidence Workspace

`ontario-grid-evidence-vault/` is MirrorArc's single, end-to-end example. It is a clean-room
data-product workspace built from public Ontario energy material, independently authored
documentation, and clearly labelled synthetic fixtures. It contains more than 50 meaningful files
across sources, contracts, pipelines, analysis, models, outputs, governance, operations, and a
small local repository fixture.

The example demonstrates:

- OGL Ontario CSV source files with exact attribution and an archive checksum.
- Metadata-only links to IESO reference pages; no IESO page body is copied.
- Word, Excel, PowerPoint, and PDF source mirroring into traceable Markdown.
- A synthetic local code repository mirrored into `20_sources/repos/`.
- A relationship-rich documentation layer for humans and agents.
- A deliberately failed synthetic model gate: 7.7% MAPE exceeds the 5% publication threshold, so
  the result remains suppressed.
- An ignored `_private-overlay/` boundary for users who want to connect private project material
  locally without placing it in this repository.

The committed snapshot is historical and educational. It is not a live view of Ontario's grid,
does not emit alerts or forecasts, and is not affiliated with or endorsed by Ontario, the IESO,
the OEB, or any private Ontario Grid project.

To exercise the example without committing generated state:

```bash
cd examples/ontario-grid-evidence-vault
python3.11 tools/mirrorarc.py plan
python3.11 tools/mirrorarc.py sync
python3.11 tools/mirrorarc.py status
python3.11 tools/mirrorarc.py lint
```

Generated mirrors, manifests, audit logs, and the private overlay remain ignored. Exact source and
licence classifications are recorded in `DATA_PROVENANCE.md`.
