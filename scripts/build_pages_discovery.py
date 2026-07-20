#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build a crawlable discovery layer around the public Pages demo portal."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime
from html import escape
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urljoin

import yaml


CATALOG_DATA_RE = re.compile(
    r'<script type="application/json" id="mirrorarc-catalog-data">(.*?)</script>',
    re.DOTALL,
)
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
WIKI_LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
SITE_TITLE = "MirrorArc Ontario Electricity Evidence Workspace"
SITE_DESCRIPTION = (
    "Explore a public, source-backed Ontario electricity documentation workspace that connects "
    "original records, generated Markdown mirrors, evidence, governance, and AI-agent context."
)
REPOSITORY_URL = "https://github.com/cz1993/MirrorArc"


@dataclass(frozen=True)
class DiscoveryDocument:
    path: str
    title: str
    slug: str
    markdown: str
    body: str
    metadata: dict[str, Any]
    description: str
    truncated: bool


def _json_for_script(value: object) -> str:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _catalog_payload(catalog_html: str) -> dict[str, Any]:
    match = CATALOG_DATA_RE.search(catalog_html)
    if not match:
        raise ValueError("catalog HTML does not contain MirrorArc catalog data")
    payload = json.loads(match.group(1))
    if not isinstance(payload, dict):
        raise ValueError("catalog data must be a JSON object")
    return payload


def _frontmatter(markdown: str) -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_RE.match(markdown.replace("\r\n", "\n").replace("\r", "\n"))
    if not match:
        return {}, markdown
    loaded = yaml.safe_load(match.group(1)) or {}
    metadata = loaded if isinstance(loaded, dict) else {}
    return metadata, markdown[match.end() :]


def _slugify(value: str) -> str:
    normalized = value.lower().replace("_", "-").replace("/", "-")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return normalized or "document"


def _plain_text(markdown: str) -> str:
    _, body = _frontmatter(markdown)
    text = re.sub(r"```.*?```", " ", body, flags=re.DOTALL)
    text = WIKI_LINK_RE.sub(lambda match: match.group(2) or match.group(1), text)
    text = MARKDOWN_LINK_RE.sub(lambda match: match.group(1), text)
    text = re.sub(r"^\s{0,3}#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_`>|~-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _description(markdown: str) -> str:
    text = _plain_text(markdown)
    if len(text) <= 158:
        return text or SITE_DESCRIPTION
    shortened = text[:158].rsplit(" ", 1)[0].rstrip(" ,.;:")
    return f"{shortened}…"


def _date_text(value: object) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()[:10]
    text = str(value or "")
    return text[:10] if re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", text) else ""


def _documents(payload: dict[str, Any]) -> list[DiscoveryDocument]:
    raw_content = payload.get("document_content", {})
    if not isinstance(raw_content, dict) or "INDEX.md" not in raw_content:
        raise ValueError("content-enabled catalog must include INDEX.md")

    used_slugs: set[str] = set()
    documents: list[DiscoveryDocument] = []
    for path in sorted(raw_content, key=lambda value: (value != "INDEX.md", value.lower())):
        content = raw_content[path]
        if not isinstance(content, dict) or not isinstance(content.get("text"), str):
            continue
        markdown = content["text"]
        metadata, body = _frontmatter(markdown)
        title = str(metadata.get("title") or Path(path).stem).strip()
        slug_base = _slugify(path.removesuffix(".md"))
        slug = slug_base
        counter = 2
        while slug in used_slugs:
            slug = f"{slug_base}-{counter}"
            counter += 1
        used_slugs.add(slug)
        documents.append(
            DiscoveryDocument(
                path=path,
                title=title,
                slug=slug,
                markdown=markdown,
                body=body,
                metadata=metadata,
                description=_description(markdown),
                truncated=bool(content.get("truncated", False)),
            )
        )
    return documents


def _aliases(documents: list[DiscoveryDocument]) -> dict[str, DiscoveryDocument]:
    aliases: dict[str, DiscoveryDocument] = {}
    for document in documents:
        values = {
            document.path,
            document.path.removesuffix(".md"),
            Path(document.path).stem,
            document.title,
        }
        for value in values:
            aliases.setdefault(value.strip().replace("\\", "/").lower(), document)
    return aliases


def _document_url(base_url: str, document: DiscoveryDocument) -> str:
    return urljoin(base_url, f"documents/{document.slug}/")


def _raw_document_url(base_url: str, document: DiscoveryDocument) -> str:
    return urljoin(base_url, f"documents/{document.slug}/index.md")


def _resolve_wiki(target: str, aliases: dict[str, DiscoveryDocument]) -> DiscoveryDocument | None:
    normalized = target.strip().replace("\\", "/").removesuffix(".md").lower()
    return aliases.get(normalized) or aliases.get(Path(normalized).stem)


def _safe_external_href(value: str) -> str:
    href = value.strip()
    return href if re.match(r"^https?://", href, flags=re.IGNORECASE) else ""


def _render_inline(value: str, aliases: dict[str, DiscoveryDocument], base_url: str) -> str:
    tokens: list[str] = []

    def token(markup: str) -> str:
        placeholder = f"MIRRORARCSTATIC{len(tokens)}END"
        tokens.append(markup)
        return placeholder

    work = re.sub(
        r"`([^`]+)`",
        lambda match: token(f"<code>{escape(match.group(1))}</code>"),
        value,
    )

    def wiki_markup(match: re.Match[str]) -> str:
        target = match.group(1).strip()
        label = (match.group(2) or target).strip()
        document = _resolve_wiki(target, aliases)
        if not document:
            return escape(label)
        return token(
            f'<a href="{escape(_document_url(base_url, document), quote=True)}">{escape(label)}</a>'
        )

    work = WIKI_LINK_RE.sub(wiki_markup, work)

    def markdown_link(match: re.Match[str]) -> str:
        label, href_value = match.group(1), match.group(2)
        href = _safe_external_href(href_value)
        if href:
            return token(f'<a href="{escape(href, quote=True)}">{escape(label)}</a>')
        document = _resolve_wiki(href_value, aliases)
        if document:
            return token(
                f'<a href="{escape(_document_url(base_url, document), quote=True)}">{escape(label)}</a>'
            )
        return f"{label} ({href_value})"

    work = MARKDOWN_LINK_RE.sub(markdown_link, work)
    rendered = escape(work)
    rendered = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", rendered)
    rendered = re.sub(r"__([^_]+)__", r"<strong>\1</strong>", rendered)
    rendered = re.sub(r"(^|\s)\*([^*]+)\*(?=\s|$|[.,;:!?])", r"\1<em>\2</em>", rendered)
    rendered = re.sub(
        r"MIRRORARCSTATIC(\d+)END",
        lambda match: tokens[int(match.group(1))] if int(match.group(1)) < len(tokens) else "",
        rendered,
    )
    return rendered


def _table_cells(row: str) -> list[str]:
    return [cell.strip() for cell in row.strip().strip("|").split("|")]


def render_markdown(markdown: str, aliases: dict[str, DiscoveryDocument], base_url: str) -> str:
    """Render the same safe Markdown subset used by the interactive explorer."""
    _, body = _frontmatter(markdown)
    lines = body.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output: list[str] = []
    paragraph: list[str] = []
    list_type = ""
    in_code = False
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{_render_inline(' '.join(paragraph), aliases, base_url)}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            output.append(f"</{list_type}>")
            list_type = ""

    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("```"):
            flush_paragraph()
            close_list()
            if in_code:
                output.append(f"<pre><code>{escape(chr(10).join(code_lines))}</code></pre>")
                code_lines.clear()
            in_code = not in_code
            index += 1
            continue
        if in_code:
            code_lines.append(line)
            index += 1
            continue
        if not line.strip():
            flush_paragraph()
            close_list()
            index += 1
            continue
        heading = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            output.append(f"<h{level}>{_render_inline(heading.group(2), aliases, base_url)}</h{level}>")
            index += 1
            continue
        if (
            "|" in line
            and index + 1 < len(lines)
            and re.match(r"^\s*\|?\s*:?-{3,}", lines[index + 1])
        ):
            flush_paragraph()
            close_list()
            header = _table_cells(line)
            index += 2
            rows: list[list[str]] = []
            while index < len(lines) and "|" in lines[index] and lines[index].strip():
                rows.append(_table_cells(lines[index]))
                index += 1
            output.append(
                "<table><thead><tr>"
                + "".join(f"<th>{_render_inline(cell, aliases, base_url)}</th>" for cell in header)
                + "</tr></thead><tbody>"
                + "".join(
                    "<tr>"
                    + "".join(f"<td>{_render_inline(cell, aliases, base_url)}</td>" for cell in row)
                    + "</tr>"
                    for row in rows
                )
                + "</tbody></table>"
            )
            continue
        bullet = re.match(r"^\s*[-*+]\s+(.+)$", line)
        ordered = re.match(r"^\s*\d+[.)]\s+(.+)$", line)
        if bullet or ordered:
            flush_paragraph()
            next_type = "ol" if ordered else "ul"
            if list_type and list_type != next_type:
                close_list()
            if not list_type:
                list_type = next_type
                output.append(f"<{list_type}>")
            match = ordered or bullet
            assert match is not None
            output.append(f"<li>{_render_inline(match.group(1), aliases, base_url)}</li>")
            index += 1
            continue
        if re.match(r"^>\s?", line):
            flush_paragraph()
            close_list()
            quote_lines = [re.sub(r"^>\s?", "", line).strip()]
            index += 1
            while index < len(lines) and lines[index].strip():
                next_line = lines[index]
                if re.match(r"^(#{1,4})\s+|^```|^\s*[-*+]\s+|^\s*\d+[.)]\s+", next_line):
                    break
                quote_lines.append(re.sub(r"^>\s?", "", next_line).strip())
                index += 1
            output.append(
                f"<blockquote>{_render_inline(' '.join(quote_lines), aliases, base_url)}</blockquote>"
            )
            continue
        if re.match(r"^\s*([-*_])(?:\s*\1){2,}\s*$", line):
            flush_paragraph()
            close_list()
            output.append("<hr>")
            index += 1
            continue
        paragraph.append(line.strip())
        index += 1

    if in_code and code_lines:
        output.append(f"<pre><code>{escape(chr(10).join(code_lines))}</code></pre>")
    flush_paragraph()
    close_list()
    return "".join(output)


def _without_leading_title(markdown: str, title: str) -> str:
    _, body = _frontmatter(markdown)
    lines = body.splitlines()
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        heading = re.match(r"^#\s+(.+)$", line.strip())
        if heading and heading.group(1).strip().lower() == title.strip().lower():
            del lines[index]
        break
    return "\n".join(lines)


STATIC_CSS = """
:root{color-scheme:light;--canvas:#fbfcfa;--panel:#fff;--ink:#213248;--muted:#6d7b8c;--line:#dce2e7;--navy:#0f3048;--teal:#007f75;--soft:#e4f5f1;font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
*{box-sizing:border-box}body{margin:0;background:var(--canvas);color:var(--ink);font-size:16px;line-height:1.65}a{color:var(--teal)}header{border-bottom:1px solid var(--line);background:var(--panel)}.topbar{width:min(1120px,calc(100% - 32px));margin:auto;min-height:64px;display:flex;align-items:center;gap:20px}.brand{font-size:22px;font-weight:750;color:var(--navy);text-decoration:none}.spacer{flex:1}.topbar nav{display:flex;gap:16px}.topbar nav a{text-decoration:none;font-weight:650}.page{width:min(900px,calc(100% - 32px));margin:42px auto 72px}.eyebrow{color:var(--teal);font-size:13px;font-weight:750;text-transform:uppercase;letter-spacing:.08em}.lede{font-size:19px;color:var(--muted)}h1,h2,h3,h4{color:var(--navy);line-height:1.2}h1{font-size:clamp(34px,6vw,54px);letter-spacing:-.035em}h2{margin-top:2em;font-size:28px}h3{margin-top:1.65em}code,pre{font-family:"SFMono-Regular",Consolas,monospace}code{background:#eef2f4;padding:.1em .35em;border-radius:4px}pre{overflow:auto;padding:18px;border:1px solid var(--line);border-radius:8px;background:#f3f6f7}blockquote{margin:24px 0;padding:14px 18px;border-left:4px solid var(--teal);background:var(--soft)}table{display:block;max-width:100%;overflow:auto;border-collapse:collapse}th,td{padding:9px 12px;border:1px solid var(--line);text-align:left}.meta{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 28px}.chip{padding:4px 9px;border:1px solid var(--line);border-radius:999px;background:var(--panel);color:var(--muted);font-size:13px}.actions{display:flex;flex-wrap:wrap;gap:12px;margin:24px 0 36px}.button{display:inline-flex;align-items:center;min-height:42px;padding:0 16px;border:1px solid var(--navy);border-radius:6px;background:var(--navy);color:#fff;text-decoration:none;font-weight:700}.button.secondary{background:#fff;color:var(--navy);border-color:var(--line)}.notice{margin:28px 0;padding:16px 18px;border:1px solid #b9e2d8;border-radius:8px;background:var(--soft)}.document-list{list-style:none;padding:0}.document-list li{margin:0;padding:18px 0;border-bottom:1px solid var(--line)}.document-list a{font-size:18px;font-weight:720;text-decoration:none}.document-list p{margin:5px 0;color:var(--muted)}footer{margin-top:60px;padding-top:22px;border-top:1px solid var(--line);color:var(--muted);font-size:14px}@media(max-width:620px){.topbar{align-items:flex-start;flex-wrap:wrap;padding:14px 0}.topbar nav{width:100%}.page{margin-top:28px}h1{font-size:36px}}
"""


def _meta_tags(*, title: str, description: str, canonical: str, page_type: str) -> str:
    values = {
        "title": title,
        "description": description,
        "canonical": canonical,
        "type": page_type,
    }
    return "".join(
        [
            f'<meta name="description" content="{escape(values["description"], quote=True)}">\n',
            '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">\n',
            f'<link rel="canonical" href="{escape(values["canonical"], quote=True)}">\n',
            '<meta name="theme-color" content="#0f3048">\n',
            f'<meta property="og:type" content="{escape(values["type"], quote=True)}">\n',
            f'<meta property="og:site_name" content="MirrorArc">\n',
            f'<meta property="og:title" content="{escape(values["title"], quote=True)}">\n',
            f'<meta property="og:description" content="{escape(values["description"], quote=True)}">\n',
            f'<meta property="og:url" content="{escape(values["canonical"], quote=True)}">\n',
            '<meta name="twitter:card" content="summary">\n',
            f'<meta name="twitter:title" content="{escape(values["title"], quote=True)}">\n',
            f'<meta name="twitter:description" content="{escape(values["description"], quote=True)}">\n',
        ]
    )


def _static_document_page(
    document: DiscoveryDocument,
    aliases: dict[str, DiscoveryDocument],
    base_url: str,
) -> str:
    canonical = _document_url(base_url, document)
    title = f"{document.title} | MirrorArc"
    metadata = document.metadata
    structured = {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": document.title,
        "description": document.description,
        "url": canonical,
        "isPartOf": {"@type": "WebSite", "name": "MirrorArc", "url": base_url},
        "author": {"@type": "Organization", "name": str(metadata.get("owner") or "MirrorArc Example")},
        "license": f"{REPOSITORY_URL}/blob/main/LICENSE",
    }
    updated = _date_text(metadata.get("updated"))
    created = _date_text(metadata.get("created"))
    if updated:
        structured["dateModified"] = updated
    if created:
        structured["datePublished"] = created

    chips = [
        str(metadata.get("domain") or "documentation"),
        str(metadata.get("type") or "note"),
        str(metadata.get("status") or "public example"),
    ]
    body = render_markdown(_without_leading_title(document.markdown, document.title), aliases, base_url)
    truncation = (
        '<div class="notice">This long record was truncated in the portable catalog. '
        "Use the repository source for the complete file.</div>"
        if document.truncated
        else ""
    )
    return "".join(
        [
            "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n",
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n',
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">\n',
            _meta_tags(title=title, description=document.description, canonical=canonical, page_type="article"),
            f'<link rel="alternate" type="text/markdown" href="{escape(_raw_document_url(base_url, document), quote=True)}">\n',
            f"<title>{escape(title)}</title>\n",
            f'<script type="application/ld+json">{_json_for_script(structured)}</script>\n',
            f"<style>{STATIC_CSS}</style>\n</head>\n<body>\n",
            '<header><div class="topbar"><a class="brand" href="../../">MirrorArc</a><span class="spacer"></span><nav>',
            '<a href="../">Documentation</a><a href="../../">Interactive portal</a>',
            f'<a href="{REPOSITORY_URL}">GitHub</a></nav></div></header>',
            '<main class="page"><p class="eyebrow">Public evidence document</p>',
            f"<h1>{escape(document.title)}</h1><p class=\"lede\">{escape(document.description)}</p>",
            '<div class="meta">',
            "".join(f'<span class="chip">{escape(chip)}</span>' for chip in chips),
            f'<span class="chip">{escape(document.path)}</span></div>',
            '<div class="actions"><a class="button" href="../../">Explore relationships</a>',
            f'<a class="button secondary" href="{escape(_raw_document_url(base_url, document), quote=True)}">Read Markdown</a></div>',
            '<article class="markdown-body">',
            body,
            truncation,
            "</article>",
            '<footer>Public MirrorArc demonstration corpus. Original records remain authoritative; generated mirrors are derived and rebuildable.</footer>',
            "</main>\n</body>\n</html>\n",
        ]
    )


def _documents_index_page(documents: list[DiscoveryDocument], base_url: str) -> str:
    canonical = urljoin(base_url, "documents/")
    description = (
        "Browse the crawlable documentation index for the MirrorArc Ontario electricity evidence "
        "workspace, including sources, contracts, analysis, governance, and runbooks."
    )
    items = "".join(
        f'<li><a href="{escape(_document_url(base_url, document), quote=True)}">{escape(document.title)}</a>'
        f'<p>{escape(document.description)}</p><span class="chip">{escape(document.path)}</span></li>'
        for document in documents
    )
    structured = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "MirrorArc public documentation index",
        "description": description,
        "url": canonical,
        "hasPart": [
            {"@type": "TechArticle", "name": document.title, "url": _document_url(base_url, document)}
            for document in documents
        ],
    }
    return "".join(
        [
            "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n",
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n',
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">\n',
            _meta_tags(
                title="MirrorArc public documentation index",
                description=description,
                canonical=canonical,
                page_type="website",
            ),
            "<title>MirrorArc public documentation index</title>\n",
            f'<script type="application/ld+json">{_json_for_script(structured)}</script>\n',
            f"<style>{STATIC_CSS}</style>\n</head>\n<body>\n",
            '<header><div class="topbar"><a class="brand" href="../">MirrorArc</a><span class="spacer"></span><nav>',
            '<a href="../">Interactive portal</a>',
            f'<a href="{REPOSITORY_URL}">GitHub</a></nav></div></header>',
            '<main class="page"><p class="eyebrow">Crawlable public corpus</p>',
            '<h1>Documentation index</h1>',
            f'<p class="lede">{escape(description)}</p>',
            f'<p>{len(documents)} public Markdown records are available as semantic HTML and raw Markdown.</p>',
            f'<ul class="document-list">{items}</ul>',
            '<footer>Built from the provenance-documented public example only. Private MirrorArc vaults remain local.</footer>',
            "</main>\n</body>\n</html>\n",
        ]
    )


def _homepage(
    catalog_html: str,
    index_document: DiscoveryDocument,
    aliases: dict[str, DiscoveryDocument],
    base_url: str,
) -> str:
    title = "MirrorArc: AI-Ready Documentation | Ontario Electricity Demo"
    structured = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "name": "MirrorArc",
                "alternateName": "MirrorArc Ontario Electricity Evidence Workspace",
                "url": base_url,
                "description": SITE_DESCRIPTION,
                "sameAs": REPOSITORY_URL,
            },
            {
                "@type": "SoftwareApplication",
                "name": "MirrorArc",
                "url": base_url,
                "description": SITE_DESCRIPTION,
                "applicationCategory": "DeveloperApplication",
                "operatingSystem": "Cross-platform",
                "isAccessibleForFree": True,
                "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
                "codeRepository": REPOSITORY_URL,
                "license": f"{REPOSITORY_URL}/blob/main/LICENSE",
            },
        ],
    }
    metadata = "".join(
        [
            _meta_tags(title=title, description=SITE_DESCRIPTION, canonical=base_url, page_type="website"),
            f'<link rel="alternate" type="text/markdown" href="{escape(urljoin(base_url, "INDEX.md"), quote=True)}" title="MirrorArc public demo index">\n',
            f'<link rel="sitemap" type="application/xml" href="{escape(urljoin(base_url, "sitemap.xml"), quote=True)}">\n',
            f'<script type="application/ld+json">{_json_for_script(structured)}</script>\n',
        ]
    )
    html = catalog_html.replace(
        "<title>MirrorArc Catalog Explorer</title>",
        f"<title>{escape(title)}</title>",
        1,
    )
    viewport = '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    if viewport not in html:
        raise ValueError("catalog HTML is missing the expected viewport metadata")
    html = html.replace(viewport, viewport + metadata, 1)

    body = render_markdown(
        _without_leading_title(index_document.markdown, index_document.title),
        aliases,
        base_url,
    )
    prerendered = "".join(
        [
            '<div class="document-view" id="document-view" data-prerendered="INDEX.md">',
            '<article class="document-sheet"><p class="doc-eyebrow">Public beginner tour · INDEX.md</p>',
            f"<h1>{escape(index_document.title)}</h1>",
            '<div class="doc-meta"><span class="status-pill">public example</span><span class="status-pill">crawlable HTML</span></div>',
            '<div class="doc-actions">',
            f'<a class="primary-button teal" href="{escape(urljoin(base_url, "documents/"), quote=True)}">Browse documentation</a>',
            f'<a class="secondary-button" href="{escape(urljoin(base_url, "INDEX.md"), quote=True)}">Read Markdown</a>',
            "</div><div class=\"markdown-body\">",
            body,
            "</div></article></div>",
        ]
    )
    placeholder = '<div class="document-view" id="document-view"></div>'
    if placeholder not in html:
        raise ValueError("catalog HTML is missing the expected document-view placeholder")
    return html.replace(placeholder, prerendered, 1)


def build_discovery_site(
    catalog_path: Path,
    output_dir: Path,
    *,
    base_url: str,
) -> dict[str, Any]:
    if not base_url.startswith("https://") or not base_url.endswith("/"):
        raise ValueError("base URL must be an absolute HTTPS URL ending in /")
    if output_dir.resolve() == Path("/"):
        raise ValueError("refusing to use / as the output directory")

    catalog_html = catalog_path.read_text(encoding="utf-8")
    payload = _catalog_payload(catalog_html)
    documents = _documents(payload)
    aliases = _aliases(documents)
    index_document = next(document for document in documents if document.path == "INDEX.md")

    output_dir.mkdir(parents=True, exist_ok=True)
    documents_dir = output_dir / "documents"
    documents_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "index.html").write_text(
        _homepage(catalog_html, index_document, aliases, base_url),
        encoding="utf-8",
    )
    (output_dir / "INDEX.md").write_text(index_document.markdown, encoding="utf-8")
    (documents_dir / "index.html").write_text(
        _documents_index_page(documents, base_url),
        encoding="utf-8",
    )

    catalog_records: list[dict[str, Any]] = []
    sitemap_records = [(base_url, _date_text(index_document.metadata.get("updated"))), (urljoin(base_url, "documents/"), "")]
    for document in documents:
        destination = documents_dir / document.slug
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "index.html").write_text(
            _static_document_page(document, aliases, base_url),
            encoding="utf-8",
        )
        (destination / "index.md").write_text(document.markdown, encoding="utf-8")
        url = _document_url(base_url, document)
        sitemap_records.append((url, _date_text(document.metadata.get("updated"))))
        catalog_records.append(
            {
                "path": document.path,
                "title": document.title,
                "type": str(document.metadata.get("type") or "note"),
                "status": str(document.metadata.get("status") or "public example"),
                "domain": str(document.metadata.get("domain") or "documentation"),
                "description": document.description,
                "html_url": url,
                "markdown_url": _raw_document_url(base_url, document),
                "truncated": document.truncated,
            }
        )

    sitemap = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n',
    ]
    for url, last_modified in sitemap_records:
        sitemap.append(f"  <url><loc>{escape(url)}</loc>")
        if last_modified:
            sitemap.append(f"<lastmod>{last_modified}</lastmod>")
        sitemap.append("</url>\n")
    sitemap.append("</urlset>\n")
    (output_dir / "sitemap.xml").write_text("".join(sitemap), encoding="utf-8")
    (output_dir / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {urljoin(base_url, 'sitemap.xml')}\n",
        encoding="utf-8",
    )

    llms_lines = [
        "# MirrorArc\n\n",
        f"> {SITE_DESCRIPTION}\n\n",
        "MirrorArc is a local-first, governed documentation layer for humans and AI agents. This hosted surface contains only the provenance-documented public Ontario electricity example.\n\n",
        "## Start here\n\n",
        f"- [Interactive portal]({base_url}): relationship map, document view, metadata, and context packs\n",
        f"- [Beginner tutorial]({urljoin(base_url, 'INDEX.md')}): raw Markdown entry point\n",
        f"- [Crawlable documentation index]({urljoin(base_url, 'documents/')}): semantic HTML pages\n",
        f"- [Agent-readable catalog]({urljoin(base_url, 'catalog.json')}): document metadata and canonical URLs\n",
        f"- [Source repository]({REPOSITORY_URL}): code, templates, tests, and provenance\n\n",
        "## Public documents\n\n",
    ]
    llms_lines.extend(
        f"- [{document.title}]({_raw_document_url(base_url, document)}): {document.description}\n"
        for document in documents
    )
    (output_dir / "llms.txt").write_text("".join(llms_lines), encoding="utf-8")
    (output_dir / "catalog.json").write_text(
        json.dumps(
            {
                "name": SITE_TITLE,
                "description": SITE_DESCRIPTION,
                "homepage": base_url,
                "repository": REPOSITORY_URL,
                "document_count": len(catalog_records),
                "documents": catalog_records,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / ".nojekyll").write_text("", encoding="utf-8")

    return {
        "documents": len(documents),
        "sitemap_urls": len(sitemap_records),
        "homepage": base_url,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog_html", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--base-url", required=True)
    args = parser.parse_args(argv)
    result = build_discovery_site(
        args.catalog_html,
        args.output_directory,
        base_url=args.base_url,
    )
    print(
        "pages discovery: "
        f"{result['documents']} documents, {result['sitemap_urls']} sitemap URLs -> {args.output_directory}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
