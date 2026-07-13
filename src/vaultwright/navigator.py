# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local, read-only browser surface for Vaultwright navigation models."""
from __future__ import annotations

import html
import json
import re
import secrets
import threading
import webbrowser
from http import HTTPStatus
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

from vaultwright.navigation import NavigationStaleError, build_navigation_model, read_document


DEFAULT_PORT = 0
LOOPBACK_HOST = "127.0.0.1"
SESSION_COOKIE = "vaultwright_navigator_session"
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
UNORDERED_RE = re.compile(r"^\s*[-*+]\s+(.+)$")
ORDERED_RE = re.compile(r"^\s*\d+[.)]\s+(.+)$")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")


def strip_frontmatter(markdown: str) -> str:
    """Remove a leading YAML frontmatter block from display content."""
    lines = markdown.splitlines()
    if not lines or lines[0].strip() != "---":
        return markdown
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[index + 1 :]).lstrip("\n")
    return markdown


def render_inline(value: str) -> str:
    """Render a deliberately small, HTML-escaped Markdown inline subset."""
    rendered = html.escape(value, quote=True)
    rendered = INLINE_CODE_RE.sub(r"<code>\1</code>", rendered)
    rendered = BOLD_RE.sub(r"<strong>\1</strong>", rendered)
    rendered = ITALIC_RE.sub(r"<em>\1</em>", rendered)
    return rendered


def heading_anchor(value: str) -> str:
    text = re.sub(r"[^a-z0-9\s-]", "", value.lower())
    return re.sub(r"[\s-]+", "-", text).strip("-") or "section"


def render_markdown(markdown: str) -> str:
    """Render a conservative Markdown subset without trusting embedded HTML."""
    lines = strip_frontmatter(markdown).splitlines()
    rendered: list[str] = []
    paragraph: list[str] = []
    list_kind: str | None = None
    in_code = False
    code_lines: list[str] = []
    used_anchors: dict[str, int] = {}

    def flush_paragraph() -> None:
        if paragraph:
            text = " ".join(part.strip() for part in paragraph)
            rendered.append(f"<p>{render_inline(text)}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_kind
        if list_kind:
            rendered.append(f"</{list_kind}>")
            list_kind = None

    for line in lines:
        if line.startswith("```"):
            flush_paragraph()
            close_list()
            if in_code:
                rendered.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
                code_lines.clear()
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line.strip():
            flush_paragraph()
            close_list()
            continue

        heading = HEADING_RE.match(line)
        if heading:
            flush_paragraph()
            close_list()
            level = min(len(heading.group(1)) + 1, 6)
            title = heading.group(2).strip()
            base_anchor = heading_anchor(title)
            count = used_anchors.get(base_anchor, 0)
            used_anchors[base_anchor] = count + 1
            anchor = base_anchor if count == 0 else f"{base_anchor}-{count + 1}"
            rendered.append(f'<h{level} id="{html.escape(anchor)}">{render_inline(title)}</h{level}>')
            continue

        unordered = UNORDERED_RE.match(line)
        ordered = ORDERED_RE.match(line)
        if unordered or ordered:
            flush_paragraph()
            next_kind = "ul" if unordered else "ol"
            if list_kind != next_kind:
                close_list()
                rendered.append(f"<{next_kind}>")
                list_kind = next_kind
            item = (unordered or ordered).group(1)
            rendered.append(f"<li>{render_inline(item)}</li>")
            continue

        if line.lstrip().startswith(">"):
            flush_paragraph()
            close_list()
            quote = line.lstrip()[1:].lstrip()
            rendered.append(f"<blockquote>{render_inline(quote)}</blockquote>")
            continue

        close_list()
        paragraph.append(line)

    if in_code:
        rendered.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
    flush_paragraph()
    close_list()
    return "\n".join(rendered)


def public_payload(root: Path) -> dict[str, Any]:
    model, warnings, errors = build_navigation_model(root)
    return {
        "model": model,
        "warnings": warnings,
        "errors": errors,
        "summary": {
            "documents": len(model.get("nodes", [])),
            "edges": len(model.get("edges", [])),
            "trails": len(model.get("trails", [])),
        },
    }


def _json_for_script(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).replace("<", "\\u003c")


def render_app(payload: dict[str, Any], session_token: str) -> str:
    """Return the self-contained Navigator application shell."""
    data = _json_for_script(payload)
    token = _json_for_script(session_token)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vaultwright Navigator</title>
<style>
:root {{ color-scheme: light; --bg: #f7f8fa; --panel: #ffffff; --text: #1f2933; --muted: #667085; --line: #d9dee7; --accent: #1f6feb; --accent-soft: #eaf2ff; --warn: #9a6700; --error: #b42318; --ok: #067647; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font: 14px/1.55 -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); }}
.skip-link {{ position: fixed; left: 12px; top: 8px; z-index: 100; transform: translateY(-160%); padding: 8px 11px; border-radius: 6px; background: #111827; color: #ffffff; }}
.skip-link:focus {{ transform: translateY(0); }}
button, input {{ font: inherit; }}
button {{ color: inherit; }}
.app-header {{ min-height: 64px; padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; gap: 16px; border-bottom: 1px solid var(--line); background: var(--panel); position: sticky; top: 0; z-index: 10; }}
.brand h1 {{ margin: 0; font-size: 20px; line-height: 1.2; }}
.brand p {{ margin: 2px 0 0; color: var(--muted); font-size: 12px; }}
.header-actions {{ display: flex; align-items: center; gap: 8px; }}
.refresh-button {{ border: 1px solid var(--line); border-radius: 7px; padding: 5px 9px; background: var(--panel); cursor: pointer; }}
.refresh-button:hover, .refresh-button:focus-visible {{ border-color: var(--accent); outline: none; }}
.local-badge {{ border: 1px solid #a6e3c4; background: #ecfdf3; color: var(--ok); border-radius: 999px; padding: 4px 9px; white-space: nowrap; }}
.layout {{ display: grid; grid-template-columns: minmax(250px, 310px) minmax(420px, 1fr) minmax(250px, 320px); min-height: calc(100vh - 65px); }}
.rail {{ padding: 18px 16px; background: var(--panel); overflow-y: auto; max-height: calc(100vh - 65px); position: sticky; top: 65px; }}
.rail-left {{ border-right: 1px solid var(--line); }}
.rail-right {{ border-left: 1px solid var(--line); }}
.reader {{ padding: 28px clamp(22px, 5vw, 72px) 80px; min-width: 0; }}
.eyebrow {{ margin: 0 0 5px; color: var(--muted); font-size: 12px; font-weight: 600; letter-spacing: .04em; text-transform: uppercase; }}
.section-title {{ margin: 22px 0 8px; font-size: 13px; }}
.section-title:first-child {{ margin-top: 0; }}
.search {{ width: 100%; border: 1px solid var(--line); border-radius: 7px; padding: 9px 10px; background: #fbfcfe; outline: none; }}
.search:focus {{ border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }}
.nav-list {{ display: grid; gap: 4px; }}
.nav-button {{ width: 100%; padding: 8px 9px; border: 0; border-radius: 6px; background: transparent; text-align: left; cursor: pointer; }}
.nav-button:hover, .nav-button:focus-visible {{ background: #f1f5f9; outline: none; }}
.nav-button.active {{ background: var(--accent-soft); color: #174ea6; font-weight: 600; }}
.nav-button small {{ display: block; color: var(--muted); font-weight: 400; overflow-wrap: anywhere; }}
.trail-card {{ border: 1px solid var(--line); border-radius: 8px; padding: 10px; margin-bottom: 8px; background: #fbfcfe; }}
.trail-card button {{ width: 100%; border: 0; padding: 0; background: transparent; text-align: left; cursor: pointer; font-weight: 600; }}
.trail-card p {{ margin: 4px 0 0; color: var(--muted); font-size: 12px; }}
.trail-outline {{ margin-top: 8px; border-top: 1px solid var(--line); padding-top: 7px; }}
.trail-outline summary {{ color: var(--accent); cursor: pointer; font-size: 12px; }}
.trail-steps {{ margin: 7px 0 0; padding-left: 22px; }}
.trail-steps li {{ margin: 3px 0; color: var(--muted); }}
.trail-steps button {{ color: var(--accent); font-size: 12px; font-weight: 400; }}
.trail-steps button[aria-current="step"] {{ color: var(--text); font-weight: 700; }}
.reader-header {{ padding-bottom: 18px; border-bottom: 1px solid var(--line); }}
.reader-header h2 {{ margin: 0 0 6px; font-size: clamp(25px, 3vw, 34px); line-height: 1.2; }}
.doc-path {{ color: var(--muted); overflow-wrap: anywhere; }}
.route-progress {{ margin-top: 14px; padding: 10px 12px; border: 1px solid #c9daf8; border-radius: 8px; background: #f7faff; }}
.route-progress strong {{ display: block; }}
.route-progress span {{ color: var(--muted); font-size: 12px; }}
.reader-controls {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 16px 0 24px; }}
.reader-controls button {{ border: 1px solid var(--line); border-radius: 7px; padding: 10px 12px; background: var(--panel); cursor: pointer; text-align: left; }}
.reader-controls button:last-child {{ text-align: right; }}
.reader-controls button:hover:not(:disabled) {{ border-color: var(--accent); }}
.reader-controls button:disabled {{ color: #98a2b3; cursor: default; }}
.document {{ max-width: 820px; font-size: 16px; line-height: 1.72; }}
.document h2, .document h3, .document h4, .document h5, .document h6 {{ line-height: 1.3; margin: 1.7em 0 .55em; scroll-margin-top: 82px; }}
.document p {{ margin: 0 0 1em; }}
.document li {{ margin: .28em 0; }}
.document blockquote {{ margin: 1em 0; padding: 9px 13px; border-left: 3px solid var(--accent); background: #f7faff; color: #344054; }}
.document pre {{ overflow: auto; padding: 14px; border: 1px solid var(--line); border-radius: 8px; background: #111827; color: #f9fafb; }}
.document code {{ padding: 1px 4px; border-radius: 4px; background: #edf1f7; font-size: .9em; }}
.document pre code {{ padding: 0; background: transparent; }}
.context-card {{ border: 1px solid var(--line); border-radius: 8px; padding: 11px; margin-bottom: 10px; background: #fbfcfe; }}
.context-card h3 {{ margin: 0 0 6px; font-size: 13px; }}
.context-card p {{ margin: 0; color: var(--muted); font-size: 12px; }}
.map-card {{ padding: 8px; }}
.map-canvas {{ display: block; width: 100%; height: 220px; border-radius: 6px; background: #f7faff; cursor: pointer; }}
.map-legend {{ display: flex; justify-content: space-between; gap: 8px; margin: 6px 3px 0 !important; }}
.context-list {{ list-style: none; margin: 0; padding: 0; display: grid; gap: 4px; }}
.context-list button {{ width: 100%; border: 0; padding: 5px 0; background: transparent; color: var(--accent); text-align: left; cursor: pointer; overflow-wrap: anywhere; }}
.meta-list {{ display: grid; grid-template-columns: minmax(70px, auto) 1fr; gap: 5px 10px; margin: 0; font-size: 12px; }}
.meta-list dt {{ color: var(--muted); }}
.meta-list dd {{ margin: 0; overflow-wrap: anywhere; }}
.notice {{ margin: 16px; padding: 10px 12px; border: 1px solid #f0d28a; border-radius: 7px; background: #fff9e8; color: var(--warn); }}
.notice.error {{ border-color: #f3b4ae; background: #fff1f0; color: var(--error); }}
.empty {{ color: var(--muted); font-style: italic; }}
@media (max-width: 1050px) {{ .layout {{ grid-template-columns: 260px 1fr; }} .rail-right {{ grid-column: 1 / -1; position: static; max-height: none; border: 1px solid var(--line); margin: 0 18px 24px; border-radius: 8px; }} }}
@media (max-width: 760px) {{ .layout {{ display: block; }} .rail {{ position: static; max-height: none; border: 0; border-bottom: 1px solid var(--line); }} .reader {{ padding: 24px 18px 48px; }} .rail-right {{ margin: 0 18px 24px; }} .app-header {{ position: static; }} }}
</style>
</head>
<body>
<a class="skip-link" href="#reader">Skip to document</a>
<header class="app-header">
  <div class="brand"><h1>Vaultwright Navigator</h1><p>Guided reading over governed Markdown</p></div>
  <div class="header-actions"><button class="refresh-button" id="rescan" type="button">Rescan</button><span class="local-badge">Local and read-only</span></div>
</header>
<div id="messages"></div>
<main class="layout">
  <aside class="rail rail-left" aria-label="Collection navigation">
    <label class="eyebrow" for="search">Find a document</label>
    <input class="search" id="search" type="search" placeholder="Search titles and paths" autocomplete="off">
    <h2 class="section-title">Guided paths</h2>
    <div id="trails"></div>
    <h2 class="section-title">Collection</h2>
    <div id="documents" class="nav-list"></div>
  </aside>
  <section class="reader" id="reader" tabindex="-1" aria-live="polite">
    <div class="reader-header">
      <p class="eyebrow" id="doc-domain">Collection</p>
      <h2 id="doc-title">Choose a document</h2>
      <div class="doc-path" id="doc-path">Select an authored path or browse the collection.</div>
      <div id="route-progress"></div>
    </div>
    <div class="reader-controls">
      <button id="previous" type="button" disabled><small>Previous</small><br><span>Start of path</span></button>
      <button id="next" type="button" disabled><small>Next</small><br><span>End of path</span></button>
    </div>
    <article id="document" class="document"><p class="empty">Document content stays in the local vault and is loaded only when selected.</p></article>
  </section>
  <aside class="rail rail-right" aria-label="Document context">
    <h2 class="section-title">Why this step</h2>
    <div id="why" class="context-card"><p>Select a guided path to see why each document follows.</p></div>
    <h2 class="section-title">Local map</h2>
    <div class="context-card map-card">
      <canvas id="local-map" class="map-canvas" role="img" aria-label="One-hop document relationship map"></canvas>
      <p class="map-legend"><span>Linked from →</span><span>→ Links to</span></p>
    </div>
    <h2 class="section-title">Document trust</h2>
    <div id="metadata" class="context-card"><p>No document selected.</p></div>
    <h2 class="section-title">Links to</h2>
    <div id="outbound" class="context-card"><p>No document selected.</p></div>
    <h2 class="section-title">Linked from</h2>
    <div id="inbound" class="context-card"><p>No document selected.</p></div>
  </aside>
</main>
<script type="application/json" id="navigator-data">{data}</script>
<script>
history.replaceState(null, '', location.pathname);
let payload = JSON.parse(document.getElementById('navigator-data').textContent);
const sessionToken = {token};
let model = payload.model || {{nodes: [], trails: []}};
let nodes = Array.isArray(model.nodes) ? model.nodes : [];
let trails = Array.isArray(model.trails) ? model.trails : [];
let nodeByPath = new Map(nodes.map(node => [node.path, node]));
let activePath = null;
let activeTrail = null;
let activeStep = -1;
let selectionVersion = 0;

function metadata(node) {{ return node.metadata || node.frontmatter || {{}}; }}
function linkPath(value) {{
  if (typeof value === 'string') return value;
  if (!value) return '';
  return value.path || value.target || value.target_path || '';
}}
function labelFor(path) {{ const node = nodeByPath.get(path); return node ? node.title : path; }}
function clear(element) {{ while (element.firstChild) element.removeChild(element.firstChild); }}
function buttonFor(path, className = '', selectionMode = 'browse', preferredTrail = null, preferredStep = null) {{
  const button = document.createElement('button');
  button.type = 'button';
  button.className = className;
  button.textContent = labelFor(path);
  button.addEventListener('click', () => selectDocument(path, preferredTrail, preferredStep, selectionMode));
  return button;
}}
function showMessages() {{
  const root = document.getElementById('messages'); clear(root);
  [...(payload.errors || []), ...(payload.warnings || [])].forEach((message, index) => {{
    const item = document.createElement('div');
    item.className = 'notice' + (index < (payload.errors || []).length ? ' error' : '');
    item.textContent = message; root.appendChild(item);
  }});
}}
function renderTrails() {{
  const root = document.getElementById('trails'); clear(root);
  if (!trails.length) {{ const empty = document.createElement('p'); empty.className = 'empty'; empty.textContent = 'No authored paths yet.'; root.appendChild(empty); return; }}
  trails.forEach(trail => {{
    const card = document.createElement('div'); card.className = 'trail-card';
    const button = document.createElement('button'); button.type = 'button'; button.textContent = trail.title || trail.id;
    button.addEventListener('click', () => startTrail(trail)); card.appendChild(button);
    const detail = document.createElement('p'); detail.textContent = `${{(trail.steps || []).length}} steps` + (trail.goal ? ` · ${{trail.goal}}` : ''); card.appendChild(detail);
    if (trail === activeTrail) {{
      const outline = document.createElement('details'); outline.className = 'trail-outline';
      const summary = document.createElement('summary'); summary.textContent = 'View ordered path'; outline.appendChild(summary);
      const list = document.createElement('ol'); list.className = 'trail-steps';
      (trail.steps || []).forEach((step, index) => {{
        const item = document.createElement('li'); const stepButton = buttonFor(step.path, '', 'trail', trail, index);
        if (index === activeStep) stepButton.setAttribute('aria-current', 'step');
        item.appendChild(stepButton); list.appendChild(item);
      }});
      outline.appendChild(list); card.appendChild(outline);
    }}
    root.appendChild(card);
  }});
}}
function renderDocuments(query = '') {{
  const root = document.getElementById('documents'); clear(root);
  const needle = query.trim().toLowerCase();
  nodes.filter(node => !needle || `${{node.title}} ${{node.path}}`.toLowerCase().includes(needle)).forEach(node => {{
    const button = buttonFor(node.path, 'nav-button' + (node.path === activePath ? ' active' : ''));
    if (node.path === activePath) button.setAttribute('aria-current', 'page');
    const path = document.createElement('small'); path.textContent = node.path; button.appendChild(path); root.appendChild(button);
  }});
  if (!root.childNodes.length) {{ const empty = document.createElement('p'); empty.className = 'empty'; empty.textContent = 'No matching documents.'; root.appendChild(empty); }}
}}
async function startTrail(trail) {{
  activeTrail = trail; activeStep = 0;
  const first = (trail.steps || [])[0];
  if (first) await selectDocument(first.path, trail, 0);
}}
function trailPosition(path, preferred) {{
  const candidates = preferred ? [preferred] : trails;
  for (const trail of candidates) {{
    const index = (trail.steps || []).findIndex(step => step.path === path);
    if (index >= 0) return [trail, index];
  }}
  return [null, -1];
}}
function updateControls() {{
  const previous = document.getElementById('previous'); const next = document.getElementById('next');
  const steps = activeTrail ? (activeTrail.steps || []) : [];
  const onTrailStep = activeStep >= 0 && steps[activeStep] && steps[activeStep].path === activePath;
  const priorIndex = onTrailStep ? activeStep - 1 : activeStep;
  const prior = priorIndex >= 0 ? steps[priorIndex] : null;
  const following = activeStep >= 0 && activeStep < steps.length - 1 ? steps[activeStep + 1] : null;
  previous.querySelector('small').textContent = onTrailStep ? 'Previous' : 'Return to path';
  previous.disabled = !prior; previous.querySelector('span').textContent = prior ? labelFor(prior.path) : 'Start of path';
  next.disabled = !following; next.querySelector('span').textContent = following ? labelFor(following.path) : 'End of path';
  previous.onclick = prior ? () => selectDocument(prior.path, activeTrail, priorIndex) : null;
  next.onclick = following ? () => selectDocument(following.path, activeTrail, activeStep + 1) : null;
}}
function renderContextList(id, values) {{
  const root = document.getElementById(id); clear(root);
  const paths = (values || []).map(linkPath).filter(path => nodeByPath.has(path));
  if (!paths.length) {{ const empty = document.createElement('p'); empty.className = 'empty'; empty.textContent = 'None in the current map.'; root.appendChild(empty); return; }}
  const list = document.createElement('ul'); list.className = 'context-list'; paths.forEach(path => {{ const item = document.createElement('li'); item.appendChild(buttonFor(path, '', 'branch')); list.appendChild(item); }}); root.appendChild(list);
}}
function mapLabel(value, limit = 20) {{
  const label = labelFor(value); return label.length > limit ? label.slice(0, limit - 1) + '…' : label;
}}
function renderMap(node) {{
  const canvas = document.getElementById('local-map');
  const box = canvas.getBoundingClientRect(); const width = Math.max(230, Math.floor(box.width)); const height = 220;
  const scale = Math.min(window.devicePixelRatio || 1, 2); canvas.width = width * scale; canvas.height = height * scale;
  const context = canvas.getContext('2d'); context.scale(scale, scale); context.clearRect(0, 0, width, height);
  const inbound = (node.inbound || []).map(linkPath).filter(path => nodeByPath.has(path)).slice(0, 4);
  const outbound = (node.outbound || []).map(linkPath).filter(path => nodeByPath.has(path)).slice(0, 4);
  const center = {{x: width / 2, y: height / 2, path: node.path, current: true}};
  const sideNodes = (paths, x, direction) => paths.map((path, index) => ({{
    path, direction, x, y: height * (index + 1) / (paths.length + 1), current: false
  }}));
  const neighbors = [...sideNodes(inbound, 48, 'inbound'), ...sideNodes(outbound, width - 48, 'outbound')];
  context.lineWidth = 1.5; context.strokeStyle = '#9fb6d9';
  neighbors.forEach(item => {{ context.beginPath(); context.moveTo(center.x, center.y); context.lineTo(item.x, item.y); context.stroke(); }});
  const drawNode = item => {{
    const nodeWidth = item.current ? Math.min(128, width * .44) : Math.min(92, width * .32); const nodeHeight = item.current ? 46 : 38;
    const left = item.x - nodeWidth / 2; const top = item.y - nodeHeight / 2;
    context.fillStyle = item.current ? '#1f6feb' : '#ffffff'; context.strokeStyle = item.current ? '#1f6feb' : '#9fb6d9'; context.lineWidth = 1.5;
    context.beginPath(); context.roundRect(left, top, nodeWidth, nodeHeight, 7); context.fill(); context.stroke();
    context.fillStyle = item.current ? '#ffffff' : '#344054'; context.font = `${{item.current ? '600 ' : ''}}11px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`; context.textAlign = 'center'; context.textBaseline = 'middle';
    context.fillText(mapLabel(item.path, item.current ? 24 : 15), item.x, item.y, nodeWidth - 10);
    return {{left, top, width: nodeWidth, height: nodeHeight, path: item.path, current: item.current}};
  }};
  canvas._hitboxes = [...neighbors.map(drawNode), drawNode(center)];
  const hidden = Math.max(0, (node.inbound || []).length - inbound.length) + Math.max(0, (node.outbound || []).length - outbound.length);
  canvas.setAttribute('aria-label', `Local map for ${{node.title}} with ${{neighbors.length}} visible connected documents${{hidden ? ` and ${{hidden}} more in the lists below` : ''}}.`);
}}
function renderMetadata(node) {{
  const root = document.getElementById('metadata'); clear(root); const data = metadata(node);
  const fields = [['Status', data.status], ['Type', data.type], ['Owner', data.owner], ['Updated', data.updated], ['Source', data.source || data.source_id || data.repo || data.repo_id]];
  const visible = fields.filter(([, value]) => value !== undefined && value !== null && value !== '');
  if (!visible.length) {{ const empty = document.createElement('p'); empty.className = 'empty'; empty.textContent = 'No trust metadata recorded.'; root.appendChild(empty); return; }}
  const list = document.createElement('dl'); list.className = 'meta-list'; visible.forEach(([label, value]) => {{ const term = document.createElement('dt'); term.textContent = label; const detail = document.createElement('dd'); detail.textContent = Array.isArray(value) ? value.join(', ') : String(value); list.append(term, detail); }}); root.appendChild(list);
}}
function renderMetadataMessage(message) {{
  const root = document.getElementById('metadata'); clear(root);
  const notice = document.createElement('p'); notice.className = 'empty'; notice.textContent = message; root.appendChild(notice);
}}
function renderRoute() {{
  const progress = document.getElementById('route-progress'); clear(progress);
  const why = document.getElementById('why'); clear(why);
  if (!activeTrail || activeStep < 0) {{ const empty = document.createElement('p'); empty.className = 'empty'; empty.textContent = 'This document is outside the active guided path.'; why.appendChild(empty); return; }}
  const step = activeTrail.steps[activeStep]; const onTrailStep = step.path === activePath; const panel = document.createElement('div'); panel.className = 'route-progress';
  const title = document.createElement('strong'); title.textContent = activeTrail.title; const detail = document.createElement('span'); detail.textContent = onTrailStep ? `Step ${{activeStep + 1}} of ${{activeTrail.steps.length}}` : `Supporting branch from step ${{activeStep + 1}} of ${{activeTrail.steps.length}}`; panel.append(title, detail); progress.appendChild(panel);
  const text = document.createElement('p'); text.textContent = onTrailStep ? (step.why || 'This authored path does not yet explain the transition.') : `This linked document branches from ${{labelFor(step.path)}}. Use Return to path to resume the authored sequence.`; why.appendChild(text);
}}
async function selectDocument(path, preferredTrail = null, preferredStep = null, selectionMode = 'browse', allowStaleRefresh = true) {{
  const node = nodeByPath.get(path); if (!node) return;
  const requestVersion = ++selectionVersion;
  activePath = path;
  if (preferredTrail && Number.isInteger(preferredStep)) {{ activeTrail = preferredTrail; activeStep = preferredStep; }}
  else if (selectionMode === 'branch' && activeTrail) {{ const [, index] = trailPosition(path, activeTrail); if (index >= 0) activeStep = index; }}
  else {{ const [trail, index] = trailPosition(path, null); activeTrail = trail; activeStep = index; }}
  renderDocuments(document.getElementById('search').value); renderTrails();
  document.getElementById('doc-title').textContent = node.title; document.getElementById('doc-path').textContent = node.path;
  document.getElementById('doc-domain').textContent = metadata(node).domain || 'Collection';
  renderRoute(); renderMap(node); renderMetadataMessage('Verifying current trust metadata…'); renderContextList('outbound', node.outbound); renderContextList('inbound', node.inbound); updateControls();
  const article = document.getElementById('document'); article.innerHTML = '<p class="empty">Loading local document…</p>';
  try {{
    const response = await fetch('/api/document?path=' + encodeURIComponent(path), {{cache: 'no-store', headers: {{'X-Vaultwright-Token': sessionToken}}}});
    if (response.status === 409 && allowStaleRefresh) {{
      if (requestVersion !== selectionVersion) return;
      await rescanNavigation();
      return;
    }}
    if (!response.ok) throw new Error('Document could not be loaded.');
    const documentPayload = await response.json(); if (requestVersion !== selectionVersion) return;
    article.innerHTML = documentPayload.html; renderMetadata(node);
  }} catch (error) {{
    if (requestVersion === selectionVersion) {{ article.textContent = error.message; renderMetadataMessage('Trust metadata is unavailable until this document can be verified.'); }}
  }}
}}
async function rescanNavigation() {{
  const button = document.getElementById('rescan');
  const snapshot = {{
    path: activePath,
    trailId: activeTrail ? activeTrail.id : null,
    step: activeStep,
    branch: Boolean(activeTrail && activeTrail.steps && activeTrail.steps[activeStep] && activeTrail.steps[activeStep].path !== activePath),
  }};
  button.disabled = true; button.textContent = 'Rescanning…';
  try {{
    const response = await fetch('/api/navigation', {{cache: 'no-store', headers: {{'X-Vaultwright-Token': sessionToken}}}});
    if (!response.ok) throw new Error('Navigation could not be rescanned.');
    payload = await response.json();
    model = payload.model || {{nodes: [], trails: []}};
    nodes = Array.isArray(model.nodes) ? model.nodes : [];
    trails = Array.isArray(model.trails) ? model.trails : [];
    nodeByPath = new Map(nodes.map(node => [node.path, node]));
    activePath = null; activeTrail = null; activeStep = -1;
    showMessages(); renderTrails(); renderDocuments(document.getElementById('search').value);
    const restoredTrail = trails.find(trail => trail.id === snapshot.trailId) || null;
    if (snapshot.path && nodeByPath.has(snapshot.path)) {{
      if (restoredTrail && Number.isInteger(snapshot.step) && snapshot.step >= 0 && snapshot.step < (restoredTrail.steps || []).length) {{
        if (snapshot.branch) {{ activeTrail = restoredTrail; activeStep = snapshot.step; await selectDocument(snapshot.path, null, null, 'branch', false); }}
        else await selectDocument(snapshot.path, restoredTrail, snapshot.step, 'trail', false);
      }} else await selectDocument(snapshot.path, null, null, 'browse', false);
    }} else if (trails.length && trails[0].steps && trails[0].steps.length) await startTrail(trails[0]);
    else if (nodes.length) await selectDocument(nodes[0].path, null, null, 'browse', false);
  }} catch (error) {{
    const root = document.getElementById('messages'); clear(root); const item = document.createElement('div'); item.className = 'notice error'; item.textContent = error.message; root.appendChild(item);
  }} finally {{ button.disabled = false; button.textContent = 'Rescan'; }}
}}
document.getElementById('search').addEventListener('input', event => renderDocuments(event.target.value));
document.getElementById('rescan').addEventListener('click', rescanNavigation);
document.getElementById('local-map').addEventListener('click', event => {{
  const canvas = event.currentTarget; const box = canvas.getBoundingClientRect(); const x = event.clientX - box.left; const y = event.clientY - box.top;
  const target = (canvas._hitboxes || []).find(item => !item.current && x >= item.left && x <= item.left + item.width && y >= item.top && y <= item.top + item.height);
  if (target) selectDocument(target.path, null, null, 'branch');
}});
window.addEventListener('resize', () => {{ if (activePath && nodeByPath.has(activePath)) renderMap(nodeByPath.get(activePath)); }});
document.addEventListener('keydown', event => {{ if (!event.altKey) return; if (event.key === 'ArrowLeft') document.getElementById('previous').click(); if (event.key === 'ArrowRight') document.getElementById('next').click(); }});
showMessages(); renderTrails(); renderDocuments();
if (trails.length && trails[0].steps && trails[0].steps.length) startTrail(trails[0]); else if (nodes.length) selectDocument(nodes[0].path);
</script>
</body>
</html>
"""


class NavigatorServer(ThreadingHTTPServer):
    """HTTP server carrying a fixed vault root and refreshable navigation model."""

    daemon_threads = True

    def __init__(self, root: Path, port: int):
        self.root = root.resolve()
        self.session_token = secrets.token_urlsafe(32)
        self.payload = public_payload(self.root)
        super().__init__((LOOPBACK_HOST, port), NavigatorHandler)

    def refresh(self) -> dict[str, Any]:
        self.payload = public_payload(self.root)
        return self.payload


class NavigatorHandler(BaseHTTPRequestHandler):
    server: NavigatorServer

    def _request_allowed(self, parsed_path: object) -> bool:
        """Reject DNS-rebinding, cross-origin, and tokenless local requests."""
        expected_host = f"{LOOPBACK_HOST}:{self.server.server_address[1]}"
        if self.headers.get("Host") != expected_host:
            return False
        origin = self.headers.get("Origin")
        if origin and origin != f"http://{expected_host}":
            return False
        if self.headers.get("Sec-Fetch-Site", "").casefold() == "cross-site":
            return False

        if not hasattr(parsed_path, "path") or not hasattr(parsed_path, "query"):
            return False
        if parsed_path.path == "/":
            query = parse_qs(parsed_path.query, keep_blank_values=True)
            if "token" in query:
                supplied = query["token"]
                token = supplied[0] if len(supplied) == 1 else ""
            else:
                cookies = SimpleCookie()
                try:
                    cookies.load(self.headers.get("Cookie", ""))
                except CookieError:
                    return False
                morsel = cookies.get(SESSION_COOKIE)
                token = morsel.value if morsel is not None else ""
        else:
            token = self.headers.get("X-Vaultwright-Token", "")
        return secrets.compare_digest(token, self.server.session_token)

    def _headers(
        self,
        content_type: str,
        length: int,
        status: HTTPStatus = HTTPStatus.OK,
        *,
        session_cookie: bool = False,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; connect-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        if session_cookie:
            self.send_header(
                "Set-Cookie",
                f"{SESSION_COOKIE}={self.server.session_token}; HttpOnly; SameSite=Strict; Path=/",
            )
        self.end_headers()

    def _send(
        self,
        body: bytes,
        content_type: str,
        status: HTTPStatus = HTTPStatus.OK,
        *,
        session_cookie: bool = False,
    ) -> None:
        self._headers(content_type, len(body), status, session_cookie=session_cookie)
        self.wfile.write(body)

    def _send_json(self, value: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(value, ensure_ascii=True, sort_keys=True).encode("utf-8")
        self._send(body, "application/json; charset=utf-8", status)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
        parsed = urlsplit(self.path)
        if not self._request_allowed(parsed):
            self._send_json({"error": "forbidden"}, HTTPStatus.FORBIDDEN)
            return
        if parsed.path == "/":
            page = render_app(self.server.refresh(), self.server.session_token).encode("utf-8")
            self._send(page, "text/html; charset=utf-8", session_cookie=True)
            return
        if parsed.path == "/api/navigation":
            self._send_json(self.server.refresh())
            return
        if parsed.path == "/api/document":
            values = parse_qs(parsed.query).get("path", [])
            if len(values) != 1:
                self._send_json({"error": "one document path is required"}, HTTPStatus.BAD_REQUEST)
                return
            payload = self.server.payload
            try:
                document = read_document(self.server.root, values[0], payload["model"])
            except NavigationStaleError as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.CONFLICT)
                return
            except (FileNotFoundError, OSError, UnicodeError, ValueError) as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
                return
            content = str(document.pop("content", ""))
            document["html"] = render_markdown(content)
            self._send_json(document)
            return
        self._send_json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: object) -> None:
        return


def serve(root: Path, *, port: int = DEFAULT_PORT, open_browser: bool = False) -> int:
    """Serve Navigator on loopback until interrupted."""
    if port < 0 or port > 65535:
        raise ValueError("port must be between 0 and 65535")
    server = NavigatorServer(root, port)
    if server.payload["errors"]:
        server.server_close()
        raise ValueError("navigation model has errors; run `vaultwright navigate --check`")
    host, selected_port = server.server_address
    url = f"http://{host}:{selected_port}/?token={server.session_token}"
    print(f"Vaultwright Navigator: {url}")
    if port != 0:
        print("Security note: prefer the default auto-selected port to avoid reusing prior browser origin state.")
    print("Read-only local view. Press Ctrl-C to stop.")
    if open_browser:
        threading.Timer(0.1, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
