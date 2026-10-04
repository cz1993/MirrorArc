# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_ontario_stress_corpus.py"


def load_module():
    spec = importlib.util.spec_from_file_location("ontario_stress", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_ieso_parser_normalizes_https_and_round_robins_series(tmp_path: Path) -> None:
    module = load_module()
    html = tmp_path / "directory.html"
    html.write_text(
        "".join(
            f'<a href="http://reports-public.ieso.ca/public/S{series}/PUB_S{series}_202607{day:02d}.xml">x</a>'
            for series in range(1, 6)
            for day in range(1, 4)
        )
        + '<a href="https://example.invalid/private.xml">ignore</a>',
        encoding="utf-8",
    )

    grouped = module.parse_ieso_links(html)
    selected = module.round_robin(grouped, 10)

    assert len(grouped) == 5
    assert len(selected) == 10
    assert len({series for series, _url in selected}) == 5
    assert all(url.startswith("https://reports-public.ieso.ca/public/") for _series, url in selected)


def test_metadata_hash_is_canonical() -> None:
    module = load_module()

    assert module.metadata_sha256({"b": 2, "a": 1}) == module.metadata_sha256({"a": 1, "b": 2})
