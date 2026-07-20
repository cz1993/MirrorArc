# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from pathlib import Path

from scripts.build_pages_discovery import build_discovery_site


BASE_URL = "https://cz1993.github.io/MirrorArc/"


def write_catalog(path: Path) -> None:
    payload = {
        "document_content_included": True,
        "document_content": {
            "INDEX.md": {
                "text": """---
title: Start here
type: hub
status: active
domain: context
created: 2026-07-19
updated: 2026-07-20
owner: MirrorArc Example
---

# Start here

This public workspace connects source records, generated mirrors, and governed knowledge.

Read [[Evidence layers and trust]] next.
""",
                "truncated": False,
            },
            "10_context/Evidence layers and trust.md": {
                "text": """---
title: Evidence layers and trust
type: note
status: active
domain: context
created: 2026-07-19
updated: 2026-07-20
owner: MirrorArc Example
---

# Evidence layers and trust

Originals are authoritative. Mirrors are derived and rebuildable.

<script>alert('not executable')</script>
""",
                "truncated": False,
            },
        },
    }
    html = "".join(
        [
            "<!doctype html><html><head>",
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n',
            "<title>MirrorArc Catalog Explorer</title></head><body>",
            '<div class="document-view" id="document-view"></div>',
            '<script type="application/json" id="mirrorarc-catalog-data">',
            json.dumps(payload, separators=(",", ":")).replace("<", "\\u003c").replace(
                ">", "\\u003e"
            ),
            "</script></body></html>",
        ]
    )
    path.write_text(html, encoding="utf-8")


def test_build_discovery_site_prerenders_index_and_crawlable_documents(tmp_path: Path) -> None:
    catalog = tmp_path / "CATALOG.html"
    output = tmp_path / "site"
    write_catalog(catalog)

    result = build_discovery_site(catalog, output, base_url=BASE_URL)

    assert result == {"documents": 2, "sitemap_urls": 4, "homepage": BASE_URL}
    homepage = (output / "index.html").read_text(encoding="utf-8")
    evidence_page = (
        output / "documents" / "10-context-evidence-layers-and-trust" / "index.html"
    ).read_text(encoding="utf-8")

    assert '<meta name="description"' in homepage
    assert f'<link rel="canonical" href="{BASE_URL}">' in homepage
    assert '<script type="application/ld+json">' in homepage
    assert 'data-prerendered="INDEX.md"' in homepage
    assert "This public workspace connects source records" in homepage
    assert (
        f'href="{BASE_URL}documents/10-context-evidence-layers-and-trust/"' in homepage
    )
    assert "Evidence layers and trust" in evidence_page
    assert "Originals are authoritative" in evidence_page
    assert "<script>alert('not executable')</script>" not in evidence_page
    assert "&lt;script&gt;alert(&#x27;not executable&#x27;)&lt;/script&gt;" in evidence_page
    assert '<link rel="alternate" type="text/markdown"' in evidence_page


def test_build_discovery_site_writes_robot_sitemap_llms_and_catalog_surfaces(tmp_path: Path) -> None:
    catalog = tmp_path / "CATALOG.html"
    output = tmp_path / "site"
    write_catalog(catalog)

    build_discovery_site(catalog, output, base_url=BASE_URL)

    robots = (output / "robots.txt").read_text(encoding="utf-8")
    sitemap = (output / "sitemap.xml").read_text(encoding="utf-8")
    llms = (output / "llms.txt").read_text(encoding="utf-8")
    agent_catalog = json.loads((output / "catalog.json").read_text(encoding="utf-8"))
    docs_index = (output / "documents" / "index.html").read_text(encoding="utf-8")

    assert "User-agent: *\nAllow: /" in robots
    assert f"Sitemap: {BASE_URL}sitemap.xml" in robots
    assert f"<loc>{BASE_URL}</loc>" in sitemap
    assert f"<loc>{BASE_URL}documents/</loc>" in sitemap
    assert sitemap.count("<url>") == 4
    assert "# MirrorArc" in llms
    assert "## Public documents" in llms
    assert f"{BASE_URL}documents/10-context-evidence-layers-and-trust/index.md" in llms
    assert agent_catalog["document_count"] == 2
    assert agent_catalog["documents"][0]["path"] == "INDEX.md"
    assert "2 public Markdown records" in docs_index


def test_build_discovery_site_rejects_non_https_or_non_directory_base_urls(tmp_path: Path) -> None:
    catalog = tmp_path / "CATALOG.html"
    write_catalog(catalog)

    for base_url in ("http://example.test/", "https://example.test/no-trailing-slash"):
        try:
            build_discovery_site(catalog, tmp_path / "site", base_url=base_url)
        except ValueError as error:
            assert "absolute HTTPS URL ending in /" in str(error)
        else:
            raise AssertionError("unsafe base URL was accepted")
