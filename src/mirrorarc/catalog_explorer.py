#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Self-contained HTML renderer for the MirrorArc metadata catalog explorer."""
from __future__ import annotations

import json
from typing import Any


def _limited(items: list[Any], max_items: int) -> tuple[list[Any], int]:
    if max_items <= 0 or len(items) <= max_items:
        return items, 0
    return items[:max_items], len(items) - max_items


def _script_json(value: object) -> str:
    """Encode JSON safely inside a non-executable script element."""
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


EXPLORER_CSS = r"""
:root {
  color-scheme: light;
  --canvas: #fbfcfa;
  --panel: #ffffff;
  --panel-soft: #f6f7f4;
  --ink: #213248;
  --muted: #6d7b8c;
  --faint: #93a0ae;
  --line: #dce2e7;
  --line-strong: #c8d1d9;
  --navy: #0f3048;
  --teal: #008f83;
  --teal-dark: #00756c;
  --teal-soft: #e4f5f1;
  --blue: #2979c9;
  --blue-soft: #edf5ff;
  --orange: #f1902f;
  --orange-soft: #fff4e7;
  --purple: #7657c8;
  --purple-soft: #f2effb;
  --mint: #4d9a77;
  --mint-soft: #edf7f1;
  --danger: #b9443e;
  --shadow-sm: 0 1px 2px rgba(26, 48, 69, 0.07);
  --shadow-md: 0 10px 30px rgba(31, 48, 69, 0.12);
  --catalog-width: 280px;
  font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

* { box-sizing: border-box; }
[hidden] { display: none !important; }
html, body { width: 100%; height: 100%; }
body {
  margin: 0;
  overflow: hidden;
  background: var(--canvas);
  color: var(--ink);
  font-size: 13px;
  line-height: 1.45;
  -webkit-font-smoothing: antialiased;
}
button, input, select { font: inherit; }
button { color: inherit; }
a { color: var(--teal-dark); text-decoration: none; }
a:hover { text-decoration: underline; }
button:focus-visible, input:focus-visible, a:focus-visible {
  outline: 2px solid var(--blue);
  outline-offset: 2px;
}
.icon {
  display: inline-block;
  width: 18px;
  height: 18px;
  flex: 0 0 auto;
  fill: currentColor;
}
.icon.small { width: 14px; height: 14px; }
.icon.large { width: 22px; height: 22px; }
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.app-shell {
  display: grid;
  grid-template-rows: 58px minmax(0, 1fr) 30px;
  width: 100vw;
  height: 100vh;
  min-width: 320px;
  overflow: hidden;
  background: var(--canvas);
}
.app-header {
  display: grid;
  grid-template-columns: 248px minmax(260px, 1fr) auto;
  align-items: center;
  gap: 18px;
  min-width: 0;
  padding: 0 18px;
  border-bottom: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.97);
  box-shadow: var(--shadow-sm);
  z-index: 30;
}
.brand-cluster { display: flex; align-items: center; gap: 16px; min-width: 0; }
.brand {
  font-family: Outfit, Inter, ui-sans-serif, sans-serif;
  font-size: 21px;
  font-weight: 700;
  letter-spacing: -0.04em;
  color: var(--navy);
  white-space: nowrap;
}
.profile-chip {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  max-width: 170px;
  gap: 8px;
  height: 34px;
  padding: 0 10px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  box-shadow: var(--shadow-sm);
  color: var(--ink);
  cursor: default;
}
.profile-chip span { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.global-search { position: relative; width: min(540px, 100%); justify-self: center; }
.global-search .icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--faint);
}
.global-search input {
  width: 100%;
  height: 34px;
  padding: 0 78px 0 38px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  color: var(--ink);
  box-shadow: inset 0 1px 1px rgba(25, 42, 57, 0.02);
}
.global-search input::placeholder { color: #99a4af; }
.keycap {
  position: absolute;
  right: 9px;
  top: 50%;
  transform: translateY(-50%);
  padding: 1px 6px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: var(--panel-soft);
  color: var(--faint);
  font-size: 10px;
}
.header-actions { display: flex; align-items: center; gap: 14px; white-space: nowrap; }
.sync-state { display: flex; align-items: center; gap: 6px; color: var(--muted); font-size: 12px; }
.sync-state .icon { color: var(--teal); }
.icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  padding: 0;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  color: var(--muted);
  cursor: pointer;
}
.icon-button:hover { background: var(--panel-soft); color: var(--ink); }
.primary-button, .secondary-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 36px;
  padding: 0 14px;
  border-radius: 5px;
  font-weight: 600;
  cursor: pointer;
}
.primary-button {
  border: 1px solid var(--navy);
  background: var(--navy);
  color: #fff;
  box-shadow: 0 2px 5px rgba(15, 48, 72, 0.16);
}
.primary-button:hover { background: #163e5a; }
.primary-button.teal { border-color: var(--teal); background: var(--teal); }
.primary-button.teal:hover { background: var(--teal-dark); }
.secondary-button { border: 1px solid var(--line); background: #fff; color: var(--ink); }
.secondary-button:hover { background: var(--panel-soft); }

.workspace {
  display: grid;
  grid-template-columns: var(--catalog-width) 6px minmax(360px, 1fr) 320px;
  min-height: 0;
  overflow: clip;
}
.left-panel, .right-panel, .center-panel { min-width: 0; min-height: 0; }
.left-panel {
  display: grid;
  grid-template-rows: auto auto auto auto minmax(0, 1fr) auto;
  background: #fff;
}
.panel-resizer {
  position: relative;
  z-index: 12;
  width: 6px;
  min-width: 6px;
  background: #fff;
  border-inline: 1px solid var(--line);
  cursor: col-resize;
  touch-action: none;
}
.panel-resizer::after {
  content: "";
  position: absolute;
  top: 50%;
  left: 50%;
  width: 2px;
  height: 36px;
  border-radius: 2px;
  background: var(--line-strong);
  transform: translate(-50%, -50%);
  transition: height 140ms ease, background 140ms ease;
}
.panel-resizer:hover::after, .panel-resizer:focus-visible::after, .panel-resizer.resizing::after {
  height: 54px;
  background: var(--teal);
}
.panel-resizer:focus-visible { outline: 2px solid var(--blue); outline-offset: -1px; }
.panel-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 4px;
  padding: 14px 12px 10px;
}
.tab-button, .segmented button, .hop-control button {
  border: 1px solid transparent;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
}
.tab-button {
  height: 32px;
  border-radius: 5px;
  font-weight: 600;
}
.tab-button[aria-selected="true"] { background: var(--panel-soft); color: var(--ink); }
.filter-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 9px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: #fff;
  color: var(--muted);
  cursor: pointer;
}
.filter-button.active { border-color: #a9d9d2; background: var(--teal-soft); color: var(--teal-dark); }
.sidebar-search { position: relative; margin: 0 12px 10px; }
.sidebar-search .icon {
  position: absolute;
  left: 9px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--faint);
}
.sidebar-search input {
  width: 100%;
  height: 31px;
  padding: 0 9px 0 31px;
  border: 0;
  border-radius: 4px;
  background: var(--panel-soft);
  color: var(--ink);
}
.filter-popover {
  display: none;
  margin: -3px 12px 10px;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  box-shadow: var(--shadow-md);
}
.filter-popover.open { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.filter-choice { display: flex; align-items: center; gap: 7px; color: var(--muted); font-size: 12px; }
.filter-choice input { accent-color: var(--teal); }
.relationship-filter-label { grid-column: 1 / -1; justify-content: space-between; }
.relationship-filter-label select { min-width: 130px; max-width: 180px; border: 1px solid var(--line); border-radius: 4px; background: #fff; color: var(--ink); }
.pinned-index { margin: 0 8px 9px; padding: 0 0 9px; border-bottom: 1px solid var(--line); }
.pinned-index-label {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 6px 6px;
  color: var(--teal-dark);
  font-size: 9px;
  font-weight: 750;
  letter-spacing: 0.11em;
  text-transform: uppercase;
}
.index-entry {
  display: grid;
  grid-template-columns: 24px minmax(0, 1fr) 16px;
  align-items: center;
  width: 100%;
  min-height: 52px;
  gap: 8px;
  padding: 8px 9px;
  border: 1px solid #b8dcd7;
  border-radius: 6px;
  background: linear-gradient(135deg, #f3fbf8 0%, #edf7f5 100%);
  color: var(--ink);
  text-align: left;
  box-shadow: var(--shadow-sm);
  cursor: pointer;
}
.index-entry:hover { border-color: var(--teal); box-shadow: 0 5px 14px rgba(0, 143, 131, 0.12); }
.index-entry.selected { border: 2px solid var(--teal); padding: 7px 8px; }
.index-entry .icon { color: var(--teal); }
.index-entry-copy { min-width: 0; }
.index-entry-title { display: block; color: var(--navy); font-size: 12px; font-weight: 750; overflow-wrap: anywhere; }
.index-entry-subtitle { display: block; margin-top: 1px; color: var(--muted); font-size: 10px; overflow-wrap: anywhere; }
.collection-scroll { overflow: auto; padding: 0 8px 14px; scrollbar-width: thin; }
.collection { margin-bottom: 5px; }
.collection-header {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 7px;
  padding: 7px 5px;
  border: 0;
  background: transparent;
  color: var(--ink);
  font-weight: 650;
  text-align: left;
  cursor: pointer;
}
.collection-header .caret { transition: transform 140ms ease; }
.collection.collapsed .collection-header .caret { transform: rotate(-90deg); }
.collection-count { margin-left: auto; color: var(--faint); font-size: 11px; font-weight: 500; }
.collection-items { display: grid; gap: 2px; }
.collection.collapsed .collection-items { display: none; }
.entity-row {
  display: grid;
  grid-template-columns: 19px minmax(0, 1fr) 16px;
  align-items: start;
  width: 100%;
  gap: 7px;
  min-height: 34px;
  padding: 5px 6px 5px 24px;
  border: 1px solid transparent;
  border-radius: 4px;
  background: transparent;
  color: var(--muted);
  text-align: left;
  cursor: pointer;
}
.entity-row:hover { background: var(--panel-soft); color: var(--ink); }
.entity-row.selected { border-color: #b7ded9; background: var(--teal-soft); color: var(--teal-dark); }
.entity-row .row-label { min-width: 0; line-height: 1.35; overflow-wrap: anywhere; white-space: normal; }
.entity-row > .icon { margin-top: 2px; }
.entity-row .status-icon { color: var(--teal); }
.entity-row.attention .status-icon { color: var(--orange); }
.sidebar-empty { padding: 22px 14px; color: var(--muted); text-align: center; }
.add-collection {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 38px;
  padding: 0 14px;
  border: 0;
  border-top: 1px solid var(--line);
  background: #fff;
  color: var(--faint);
  cursor: pointer;
}
.add-collection:hover { color: var(--ink); }

.center-panel {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr);
  overflow: hidden;
  background: var(--canvas);
}
.center-toolbar {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 54px;
  padding: 10px 18px;
  border-bottom: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.88);
}
.segmented {
  display: inline-grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  width: min(100%, 390px);
  height: 34px;
  border: 1px solid var(--line);
  border-radius: 5px;
  overflow: hidden;
  background: var(--panel-soft);
}
.segmented button { padding: 0 12px; font-size: 11px; font-weight: 600; white-space: nowrap; }
.segmented button[aria-selected="true"] { background: var(--teal); color: #fff; }
.tab-label-short { display: none; }
.toolbar-spacer { flex: 1; }
.fit-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 10px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: #fff;
  color: var(--muted);
  cursor: pointer;
}
.fit-button:hover { color: var(--ink); background: var(--panel-soft); }
.mobile-panel-button { display: none; }
.map-view {
  display: grid;
  grid-template-rows: 48px minmax(0, 1fr) 56px;
  min-height: 0;
  overflow: hidden;
}
.map-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 18px 6px;
  color: var(--muted);
  font-size: 11px;
}
.map-controls strong { color: var(--ink); font-size: 11px; }
.hop-control {
  display: inline-grid;
  grid-template-columns: repeat(3, 52px);
  height: 30px;
  border: 1px solid var(--line);
  border-radius: 5px;
  overflow: hidden;
  background: #fff;
}
.hop-control button { border-right: 1px solid var(--line); font-size: 11px; }
.hop-control button:last-child { border-right: 0; }
.hop-control button[aria-pressed="true"] { background: var(--teal); color: #fff; }
.map-hint { margin-left: auto; color: var(--faint); }
.graph-viewport {
  position: relative;
  min-height: 0;
  overflow: auto;
  background-color: var(--canvas);
  background-image: radial-gradient(circle at 1px 1px, rgba(109, 123, 140, 0.15) 1px, transparent 0);
  background-size: 22px 22px;
  scrollbar-width: thin;
}
.graph-stage-space { position: relative; margin: 0 auto; }
.graph-stage {
  position: absolute;
  left: 0;
  top: 0;
  width: 1200px;
  height: 650px;
  transform-origin: top left;
}
.edge-layer { position: absolute; inset: 0; z-index: 2; overflow: visible; pointer-events: none; }
.edge-path {
  fill: none;
  stroke: #7e91a3;
  stroke-width: 1.25;
  opacity: 0.34;
  transition: opacity 160ms ease, stroke 160ms ease, stroke-width 160ms ease;
}
.edge-path.is-focus, .edge-path.is-hover { stroke: var(--teal); stroke-width: 2; opacity: 1; }
.edge-label-bg { fill: rgba(251, 252, 250, 0.95); stroke: #e3e7ea; stroke-width: 0.7; }
.edge-label { fill: #6e7c8b; font-size: 10px; font-weight: 650; letter-spacing: 0.03em; }
.edge-label-group { opacity: 0.96; }
.graph-group {
  position: absolute;
  z-index: 1;
  border: 1px dashed var(--line-strong);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.5);
  pointer-events: none;
}
.graph-group.domain-source { border-color: #bcd8f4; background: rgba(237, 245, 255, 0.36); }
.graph-group.domain-mirror { border-color: #b8ddd7; background: rgba(228, 245, 241, 0.34); }
.graph-group.domain-curated { border-color: #c9d9ef; background: rgba(243, 247, 252, 0.4); }
.graph-group.domain-governance { border-color: #bee2d2; background: rgba(237, 247, 241, 0.42); }
.graph-group-label {
  position: absolute;
  left: 10px;
  top: 8px;
  color: var(--blue);
  font-size: 11px;
  font-weight: 700;
}
.entity-card {
  position: absolute;
  display: grid;
  grid-template-columns: 30px minmax(0, 1fr) 16px;
  align-items: center;
  width: 214px;
  min-height: 88px;
  gap: 8px;
  padding: 10px 9px;
  border: 1px solid var(--line-strong);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.98);
  color: var(--ink);
  text-align: left;
  box-shadow: 0 2px 5px rgba(39, 58, 76, 0.08);
  cursor: pointer;
  z-index: 4;
  transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease, opacity 160ms ease;
  animation: node-enter 220ms ease both;
}
.entity-card:hover { border-color: #63aaa2; box-shadow: 0 7px 18px rgba(39, 58, 76, 0.15); transform: translateY(-2px); }
.entity-card.selected { border: 2px solid var(--teal); box-shadow: 0 5px 16px rgba(0, 143, 131, 0.2); }
.entity-card .node-icon { color: var(--teal); }
.entity-card.kind-source .node-icon, .entity-card.kind-repo .node-icon { color: var(--blue); }
.entity-card.kind-review .node-icon { color: var(--purple); }
.entity-card.kind-pack .node-icon { color: var(--mint); }
.entity-card.kind-domain .node-icon { color: var(--orange); }
.node-copy { min-width: 0; }
.node-title {
  display: -webkit-box;
  overflow: hidden;
  color: var(--ink);
  font-size: 11px;
  font-weight: 700;
  line-height: 1.25;
  overflow-wrap: anywhere;
  white-space: normal;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}
.node-subtitle {
  display: block;
  overflow: hidden;
  margin-top: 2px;
  color: var(--muted);
  font-size: 9px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.node-status { color: var(--teal); }
.entity-card.attention .node-status { color: var(--orange); }
@keyframes node-enter {
  from { opacity: 0; transform: translateY(8px) scale(0.985); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
.graph-empty {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 280px;
  transform: translate(-50%, -50%);
  color: var(--muted);
  text-align: center;
}
.zoom-controls {
  position: absolute;
  right: 14px;
  bottom: 16px;
  display: grid;
  border: 1px solid var(--line);
  border-radius: 6px;
  overflow: hidden;
  background: #fff;
  box-shadow: var(--shadow-sm);
  z-index: 8;
}
.zoom-controls button {
  width: 34px;
  height: 32px;
  border: 0;
  border-bottom: 1px solid var(--line);
  background: #fff;
  color: var(--muted);
  cursor: pointer;
}
.zoom-controls button:last-child { border-bottom: 0; }
.zoom-controls button:hover { background: var(--panel-soft); color: var(--ink); }
.legend {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18px;
  padding: 10px 14px;
  border-top: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.94);
  color: var(--muted);
  font-size: 10px;
}
.legend-item { display: inline-flex; align-items: center; gap: 5px; white-space: nowrap; }
.legend-item .icon { width: 14px; height: 14px; }
.legend-item.source .icon { color: var(--blue); }
.legend-item.mirror .icon { color: var(--teal); }
.legend-item.review .icon { color: var(--purple); }
.legend-item.pack .icon { color: var(--mint); }

.document-view {
  min-height: 0;
  overflow: auto;
  padding: 30px clamp(24px, 7vw, 86px) 56px;
  background: #f7f8f6;
}
.document-sheet {
  max-width: 820px;
  min-width: 0;
  min-height: calc(100% - 10px);
  margin: 0 auto;
  padding: 44px 56px 60px;
  border: 1px solid var(--line);
  border-radius: 7px;
  background: #fff;
  box-shadow: 0 10px 32px rgba(31, 48, 69, 0.08);
}
.doc-eyebrow { margin: 0 0 10px; color: var(--teal-dark); font-size: 11px; font-weight: 750; letter-spacing: 0.08em; text-transform: uppercase; }
.document-sheet h1 { margin: 0; overflow-wrap: anywhere; color: var(--navy); font-family: Outfit, Inter, sans-serif; font-size: 32px; line-height: 1.15; letter-spacing: -0.035em; }
.doc-meta { display: flex; flex-wrap: wrap; gap: 8px; margin: 14px 0 28px; }
.document-sheet h2 { margin: 30px 0 10px; color: var(--ink); font-size: 17px; }
.document-sheet p { margin: 0 0 12px; color: #435468; font-size: 14px; line-height: 1.7; }
.document-sheet ul { margin: 8px 0 0; padding-left: 20px; color: #435468; }
.document-sheet li { margin: 7px 0; }
.doc-callout { margin: 22px 0; padding: 15px 17px; border-left: 3px solid var(--teal); background: var(--teal-soft); color: #345b57; }
.doc-actions { display: flex; flex-wrap: wrap; gap: 9px; margin: 20px 0 26px; }
.doc-actions button { min-height: 36px; }
.doc-path { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 12px; overflow-wrap: anywhere; }
.answer-review { border-top: 1px solid var(--border); margin-top: 18px; padding-top: 12px; }
.answer-text { white-space: pre-wrap; overflow-wrap: anywhere; }
pre.doc-path { white-space: pre-wrap; max-width: 100%; }
.metadata-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin: 16px 0; }
.metadata-card { padding: 12px; border: 1px solid var(--line); border-radius: 5px; background: var(--panel-soft); }
.metadata-card span { display: block; color: var(--faint); font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em; }
.metadata-card strong { display: block; margin-top: 3px; color: var(--ink); font-size: 13px; overflow-wrap: anywhere; }
.code-dashboard { display: grid; gap: 18px; }
.code-hero { padding: 20px; border: 1px solid var(--line); border-radius: 7px; background: linear-gradient(135deg, var(--blue-soft), #fff 62%); }
.code-hero h2 { margin: 4px 0 8px; font-size: 22px; }
.code-hero p { margin-bottom: 0; }
.code-kpis { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.code-kpi { min-width: 0; padding: 13px; border: 1px solid var(--line); border-radius: 6px; background: var(--panel-soft); }
.code-kpi span { display: block; color: var(--muted); font-size: 10px; text-transform: uppercase; letter-spacing: 0.05em; }
.code-kpi strong { display: block; margin-top: 5px; color: var(--navy); font-size: 17px; overflow-wrap: anywhere; }
.code-section { min-width: 0; padding: 18px; border: 1px solid var(--line); border-radius: 7px; background: #fff; }
.code-section > h2 { margin: 0 0 12px; }
.code-table-wrap { max-width: 100%; overflow-x: auto; }
.code-table { width: 100%; border-collapse: collapse; font-size: 11px; }
.code-table th, .code-table td { padding: 9px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
.code-table th { color: var(--muted); font-size: 9px; text-transform: uppercase; letter-spacing: 0.05em; }
.code-table td { overflow-wrap: anywhere; }
.code-path-list { display: grid; gap: 7px; margin: 0; padding: 0; list-style: none; counter-reset: code-path; }
.code-path-list li { display: grid; grid-template-columns: 24px minmax(0, 1fr); gap: 9px; align-items: start; margin: 0; }
.code-path-list li::before { counter-increment: code-path; content: counter(code-path); display: grid; place-items: center; width: 22px; height: 22px; border-radius: 50%; background: var(--teal-soft); color: var(--teal-dark); font-size: 10px; font-weight: 750; }
.code-path-list strong, .code-path-list span { overflow-wrap: anywhere; }
.code-warning-list { display: grid; gap: 8px; }
.code-warning { padding: 10px 12px; border-left: 3px solid var(--orange); background: var(--orange-soft); color: #77512b; overflow-wrap: anywhere; }
.code-command { display: flex; align-items: center; gap: 8px; min-width: 0; margin-top: 12px; padding: 10px; border: 1px solid var(--line); border-radius: 5px; background: #16283a; color: #eef4f7; }
.code-command code { min-width: 0; flex: 1; overflow-wrap: anywhere; white-space: normal; }
pre.code-command { display: block; white-space: pre-wrap; overflow-wrap: anywhere; }
#governed-contexts { overflow-wrap: anywhere; }
.code-command button { flex: 0 0 auto; }
.code-excerpt { max-height: 220px; overflow: auto; margin: 8px 0 0; padding: 11px; border-radius: 5px; background: #16283a; color: #eef4f7; white-space: pre-wrap; overflow-wrap: anywhere; font: 11px/1.55 ui-monospace, SFMono-Regular, Menlo, monospace; }
.markdown-body { min-width: 0; color: #34465a; font-size: 14px; line-height: 1.72; overflow-wrap: anywhere; }
.markdown-body > :first-child { margin-top: 0; }
.markdown-body h1, .markdown-body h2, .markdown-body h3, .markdown-body h4 {
  color: var(--navy);
  font-family: Outfit, Inter, ui-sans-serif, sans-serif;
  line-height: 1.25;
  letter-spacing: -0.02em;
}
.markdown-body h1 { margin: 0 0 18px; font-size: 30px; }
.markdown-body h2 { margin: 34px 0 12px; padding-bottom: 8px; border-bottom: 1px solid var(--line); font-size: 21px; }
.markdown-body h3 { margin: 26px 0 9px; font-size: 17px; }
.markdown-body p { margin: 0 0 14px; color: #435468; }
.markdown-body ul, .markdown-body ol { margin: 8px 0 18px; padding-left: 24px; }
.markdown-body blockquote { margin: 18px 0; padding: 10px 16px; border-left: 3px solid var(--blue); background: var(--blue-soft); color: #365a7c; }
.markdown-body code { padding: 2px 5px; border: 1px solid #e1e6ea; border-radius: 4px; background: var(--panel-soft); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.92em; }
.markdown-body pre { overflow: auto; margin: 18px 0; padding: 15px; border-radius: 6px; background: #16283a; color: #edf4f7; }
.markdown-body pre code { padding: 0; border: 0; background: transparent; color: inherit; }
.markdown-body table { display: block; width: 100%; max-width: 100%; overflow-x: auto; margin: 18px 0; border-collapse: collapse; font-size: 12px; }
.markdown-body th, .markdown-body td { padding: 9px 10px; border: 1px solid var(--line); text-align: left; vertical-align: top; }
.markdown-body th { background: var(--panel-soft); color: var(--ink); }
.wiki-link {
  display: inline;
  padding: 0;
  border: 0;
  border-bottom: 1px solid rgba(0, 117, 108, 0.35);
  background: transparent;
  color: var(--teal-dark);
  cursor: pointer;
}
.wiki-link:hover { border-bottom-color: var(--teal-dark); }
.wiki-link:disabled { border-bottom-style: dotted; color: var(--muted); cursor: default; }
.content-unavailable { padding: 28px; border: 1px dashed var(--line-strong); border-radius: 7px; background: var(--panel-soft); text-align: center; }
.content-unavailable .icon { color: var(--teal); }

.right-panel {
  display: grid;
  grid-template-rows: 54px minmax(0, 1fr);
  border-left: 1px solid var(--line);
  background: #fff;
}
.inspector-header { display: flex; align-items: center; gap: 8px; padding: 0 14px; border-bottom: 1px solid var(--line); }
.inspector-header h2 { margin: 0; font-size: 15px; font-weight: 750; }
.inspector-header .spacer { flex: 1; }
.plain-icon-button { display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; padding: 0; border: 0; background: transparent; color: var(--muted); cursor: pointer; }
.plain-icon-button:hover { color: var(--ink); }
.inspector-scroll { overflow: auto; scrollbar-width: thin; }
.inspector-identity { display: grid; grid-template-columns: 34px minmax(0, 1fr) auto; align-items: center; gap: 9px; padding: 15px 14px; border-bottom: 1px solid var(--line); }
.inspector-identity .identity-icon { color: var(--teal); }
.identity-title { font-size: 14px; font-weight: 750; line-height: 1.25; overflow-wrap: anywhere; }
.identity-subtitle { color: var(--muted); font-size: 10px; overflow-wrap: anywhere; }
.status-pill { display: inline-flex; align-items: center; gap: 4px; min-height: 20px; padding: 1px 7px; border: 1px solid #b6dac6; border-radius: 4px; background: var(--mint-soft); color: #267254; font-size: 10px; white-space: nowrap; }
.status-pill.attention { border-color: #f0c28e; background: var(--orange-soft); color: #a35c15; }
.inspector-section { border-bottom: 1px solid var(--line); }
.inspector-section-title { display: flex; align-items: center; gap: 7px; min-height: 39px; padding: 0 14px; color: var(--ink); font-size: 11px; font-weight: 750; }
.inspector-section-title .spacer { flex: 1; }
.inspector-section-body { padding: 0 14px 13px; }
.inspector-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; padding: 6px 0; color: var(--muted); font-size: 10px; }
.inspector-row strong { color: var(--ink); font-weight: 600; text-align: right; overflow-wrap: anywhere; }
.provenance-path { display: grid; gap: 5px; color: var(--muted); font-size: 10px; }
.provenance-path a, .provenance-path span { overflow-wrap: anywhere; }
.provenance-path span::before { content: ">"; margin-right: 7px; color: var(--faint); }
.relationship-list { display: grid; gap: 2px; }
.relationship-row {
  display: grid;
  grid-template-columns: 17px minmax(0, 1fr) auto;
  align-items: center;
  width: 100%;
  min-height: 30px;
  gap: 6px;
  padding: 3px 0;
  border: 0;
  background: transparent;
  color: var(--muted);
  font-size: 10px;
  text-align: left;
  cursor: pointer;
}
.relationship-row:hover { color: var(--ink); }
.relationship-row .rel-title { line-height: 1.3; overflow-wrap: anywhere; }
.relationship-row .rel-kind { color: var(--faint); font-size: 9px; }
.relationship-row .rel-state { color: var(--teal); font-size: 9px; font-weight: 700; text-transform: capitalize; }
.relationship-governance { display: grid; gap: 7px; }
.relationship-decision { padding: 8px 0; border-top: 1px solid var(--line); }
.relationship-decision:first-child { border-top: 0; }
.relationship-decision-head { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; color: var(--ink); font-size: 10px; }
.relationship-decision-head strong { overflow-wrap: anywhere; }
.relationship-decision-state { color: var(--teal); font-size: 9px; font-weight: 750; text-transform: capitalize; }
.relationship-decision-meta { margin-top: 3px; color: var(--muted); font-size: 9px; line-height: 1.45; overflow-wrap: anywhere; }
.inspector-actions { display: grid; gap: 8px; padding: 14px; }
.inspector-actions button { width: 100%; }
.safety-note { padding: 10px 12px; border: 1px solid #f0d4ad; border-radius: 5px; background: #fff9ef; color: #805c2f; font-size: 10px; }

.status-bar {
  display: flex;
  align-items: center;
  gap: 18px;
  min-width: 0;
  overflow: hidden;
  padding: 0 16px;
  border-top: 1px solid var(--line);
  background: #fff;
  color: var(--muted);
  font-size: 10px;
  z-index: 20;
}
.status-bar span { white-space: nowrap; }
.status-bar .separator { color: var(--line-strong); }
.status-bar .authority { margin-left: auto; overflow: hidden; text-overflow: ellipsis; }

.toast {
  position: fixed;
  left: 50%;
  bottom: 48px;
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 8px;
  max-width: min(420px, calc(100vw - 30px));
  padding: 10px 14px;
  border-radius: 6px;
  background: var(--navy);
  color: #fff;
  box-shadow: var(--shadow-md);
  transform: translate(-50%, 20px);
  opacity: 0;
  pointer-events: none;
  transition: opacity 150ms ease, transform 150ms ease;
}
.toast.show { opacity: 1; transform: translate(-50%, 0); }
.modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: none;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(22, 38, 53, 0.4);
  backdrop-filter: blur(3px);
}
.modal-backdrop.open { display: flex; }
.modal {
  width: min(620px, 100%);
  max-height: min(720px, calc(100vh - 40px));
  overflow: auto;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 24px 70px rgba(15, 48, 72, 0.25);
}
.modal-header { display: flex; align-items: center; gap: 12px; padding: 18px 20px; border-bottom: 1px solid var(--line); }
.modal-header h2 { margin: 0; font-size: 18px; }
.modal-header .spacer { flex: 1; }
.modal-body { padding: 20px; }
.modal-body p { color: var(--muted); }
.pack-list { display: grid; gap: 7px; margin: 16px 0; }
.pack-item { display: grid; grid-template-columns: 22px minmax(0, 1fr) auto; align-items: center; gap: 9px; padding: 10px; border: 1px solid var(--line); border-radius: 5px; background: var(--panel-soft); }
.pack-item strong { overflow-wrap: anywhere; }
.pack-item span { color: var(--faint); font-size: 10px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; padding: 15px 20px; border-top: 1px solid var(--line); }
.mobile-backdrop { display: none; }

@media (max-width: 1120px) {
  .workspace { grid-template-columns: var(--catalog-width) 6px minmax(340px, 1fr); }
  .app-header { grid-template-columns: 220px minmax(220px, 1fr) auto; }
  .profile-chip { max-width: 145px; }
  .sync-state span { display: none; }
  .right-panel {
    position: fixed;
    top: 58px;
    right: 0;
    bottom: 30px;
    z-index: 70;
    width: min(360px, calc(100vw - 42px));
    font-size: 12px;
    box-shadow: var(--shadow-md);
    transform: translateX(105%);
    transition: transform 180ms ease;
  }
  .right-panel.open { transform: translateX(0); }
  #open-right { display: inline-flex; align-items: center; height: 32px; padding: 0 9px; border: 1px solid var(--line); border-radius: 5px; background: #fff; color: var(--muted); cursor: pointer; }
  .mobile-backdrop { position: fixed; inset: 58px 0 30px; z-index: 65; background: rgba(21, 38, 53, 0.32); }
  .mobile-backdrop.open { display: block; }
  .segmented { width: min(100%, 300px); }
  .segmented button { padding-inline: 7px; }
  .tab-label-long { display: none; }
  .tab-label-short { display: inline; }
}

@media (max-width: 820px) {
  .app-shell { grid-template-rows: 54px minmax(0, 1fr) 28px; }
  .app-header { grid-template-columns: auto 1fr auto; gap: 10px; padding: 0 12px; }
  .profile-chip, .global-search, .sync-state, .help-button { display: none; }
  .header-actions { justify-self: end; gap: 8px; }
  .header-actions .primary-button { width: 36px; padding: 0; font-size: 0; }
  .header-actions .primary-button .icon { width: 18px; height: 18px; }
  .workspace { grid-template-columns: minmax(0, 1fr); }
  .panel-resizer { display: none; }
  .left-panel, .right-panel {
    position: fixed;
    top: 54px;
    bottom: 28px;
    z-index: 70;
    width: min(330px, calc(100vw - 38px));
    box-shadow: var(--shadow-md);
    transition: transform 180ms ease;
  }
  .left-panel { left: 0; transform: translateX(-105%); }
  .right-panel { right: 0; transform: translateX(105%); }
  .left-panel.open, .right-panel.open { transform: translateX(0); }
  .mobile-backdrop { position: fixed; inset: 54px 0 28px; z-index: 65; background: rgba(21, 38, 53, 0.32); }
  .mobile-backdrop.open { display: block; }
  .mobile-panel-button { display: inline-flex; align-items: center; gap: 5px; height: 32px; padding: 0 8px; border: 1px solid var(--line); border-radius: 5px; background: #fff; color: var(--muted); cursor: pointer; }
  .center-toolbar { padding: 8px 10px; gap: 7px; }
  .segmented { width: min(100%, 360px); }
  .fit-button span { display: none; }
  .map-controls { padding-inline: 10px; }
  .map-hint { display: none; }
  .legend { justify-content: flex-start; overflow-x: auto; }
  .document-view { padding: 14px; }
  .document-sheet { padding: 30px 24px 42px; }
  .document-sheet h1 { font-size: 26px; }
  .metadata-grid { grid-template-columns: 1fr; }
  .code-kpis { grid-template-columns: 1fr; }
  .code-section { padding: 14px; }
  .code-command { align-items: stretch; flex-direction: column; }
  .status-bar { gap: 8px; padding-inline: 10px; }
  .status-bar .authority { display: none; }
}

@media (max-width: 480px) {
  .brand { font-size: 18px; }
  .center-toolbar { flex-wrap: wrap; min-height: 82px; }
  .segmented { order: 1; width: 100%; }
  .mobile-panel-button { order: 2; }
  .toolbar-spacer { display: none; }
  .fit-button { order: 2; margin-left: auto; }
  .map-controls { gap: 8px; }
  .hop-control { grid-template-columns: repeat(3, 47px); }
  .map-view { grid-template-rows: 48px minmax(0, 1fr) 48px; }
  .legend { gap: 12px; }
  .legend-item.review { display: none; }
  .status-bar .separator, .status-bar .hidden-count { display: none; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; transition-duration: 0.01ms !important; }
}
"""


EXPLORER_JS = r"""
(() => {
  "use strict";

  window.__mirrorarcRuntimeErrors = [];
  window.addEventListener("error", (event) => window.__mirrorarcRuntimeErrors.push(String(event.message || event.error || "window error")));
  window.addEventListener("unhandledrejection", (event) => window.__mirrorarcRuntimeErrors.push(String(event.reason || "unhandled rejection")));

  const data = JSON.parse(document.getElementById("mirrorarc-catalog-data").textContent);
  const projectionData = data.knowledge_projection && typeof data.knowledge_projection === "object" ? data.knowledge_projection : {};
  const codeData = data.code_intelligence && typeof data.code_intelligence === "object" ? data.code_intelligence : {repositories: []};
  const iconPaths = {
    fileMd: "M213.66,82.34l-56-56A8,8,0,0,0,152,24H56A16,16,0,0,0,40,40v72a8,8,0,0,0,16,0V40h88V88a8,8,0,0,0,8,8h48V224a8,8,0,0,0,16,0V88A8,8,0,0,0,213.66,82.34ZM160,51.31,188.69,80H160ZM144,144H128a8,8,0,0,0-8,8v56a8,8,0,0,0,8,8h16a36,36,0,0,0,0-72Zm0,56h-8V160h8a20,20,0,0,1,0,40Zm-40-48v56a8,8,0,0,1-16,0V177.38L74.55,196.59a8,8,0,0,1-13.1,0L48,177.38V208a8,8,0,0,1-16,0V152a8,8,0,0,1,14.55-4.59L68,178.05l21.45-30.64A8,8,0,0,1,104,152Z",
    fileDoc: "M52,144H36a8,8,0,0,0-8,8v56a8,8,0,0,0,8,8H52a36,36,0,0,0,0-72Zm0,56H44V160h8a20,20,0,0,1,0,40Zm169.53-4.91a8,8,0,0,1,.25,11.31A30.06,30.06,0,0,1,200,216c-17.65,0-32-16.15-32-36s14.35-36,32-36a30.06,30.06,0,0,1,21.78,9.6,8,8,0,0,1-11.56,11.06A14.24,14.24,0,0,0,200,160c-8.82,0-16,9-16,20s7.18,20,16,20a14.24,14.24,0,0,0,10.22-4.66A8,8,0,0,1,221.53,195.09ZM128,144c-17.65,0-32,16.15-32,36s14.35,36,32,36,32-16.15,32-36S145.65,144,128,144Zm0,56c-8.82,0-16-9-16-20s7.18-20,16-20,16,9,16,20S136.82,200,128,200ZM48,120a8,8,0,0,0,8-8V40h88V88a8,8,0,0,0,8,8h48v16a8,8,0,0,0,16,0V88a8,8,0,0,0-2.34-5.66l-56-56A8,8,0,0,0,152,24H56A16,16,0,0,0,40,40v72A8,8,0,0,0,48,120ZM160,51.31,188.69,80H160Z",
    folder: "M216,72H130.67L102.93,51.2a16.12,16.12,0,0,0-9.6-3.2H40A16,16,0,0,0,24,64V200a16,16,0,0,0,16,16H216.89A15.13,15.13,0,0,0,232,200.89V88A16,16,0,0,0,216,72Zm0,128H40V64H93.33L123.2,86.4A8,8,0,0,0,128,88h88Z",
    search: "M229.66,218.34l-50.07-50.06a88.11,88.11,0,1,0-11.31,11.31l50.06,50.07a8,8,0,0,0,11.32-11.32ZM40,112a72,72,0,1,1,72,72A72.08,72.08,0,0,1,40,112Z",
    filter: "M200,136a8,8,0,0,1-8,8H64a8,8,0,0,1,0-16H192A8,8,0,0,1,200,136Zm32-56H24a8,8,0,0,0,0,16H232a8,8,0,0,0,0-16Zm-80,96H104a8,8,0,0,0,0,16h48a8,8,0,0,0,0-16Z",
    fit: "M216,48V96a8,8,0,0,1-16,0V67.31l-50.34,50.35a8,8,0,0,1-11.32-11.32L188.69,56H160a8,8,0,0,1,0-16h48A8,8,0,0,1,216,48ZM106.34,138.34,56,188.69V160a8,8,0,0,0-16,0v48a8,8,0,0,0,8,8H96a8,8,0,0,0,0-16H67.31l50.35-50.34a8,8,0,0,0-11.32-11.32Z",
    check: "M173.66,98.34a8,8,0,0,1,0,11.32l-56,56a8,8,0,0,1-11.32,0l-24-24a8,8,0,0,1,11.32-11.32L112,148.69l50.34-50.35A8,8,0,0,1,173.66,98.34ZM232,128A104,104,0,1,1,128,24,104.11,104.11,0,0,1,232,128Zm-16,0a88,88,0,1,0-88,88A88.1,88.1,0,0,0,216,128Z",
    warning: "M236.8,188.09,149.35,36.22h0a24.76,24.76,0,0,0-42.7,0L19.2,188.09a23.51,23.51,0,0,0,0,23.72A24.35,24.35,0,0,0,40.55,224h174.9a24.35,24.35,0,0,0,21.33-12.19A23.51,23.51,0,0,0,236.8,188.09ZM222.93,203.8a8.5,8.5,0,0,1-7.48,4.2H40.55a8.5,8.5,0,0,1-7.48-4.2,7.59,7.59,0,0,1,0-7.72L120.52,44.21a8.75,8.75,0,0,1,15,0l87.45,151.87A7.59,7.59,0,0,1,222.93,203.8ZM120,144V104a8,8,0,0,1,16,0v40a8,8,0,0,1-16,0Zm20,36a12,12,0,1,1-12-12A12,12,0,0,1,140,180Z",
    stack: "M230.91,172A8,8,0,0,1,228,182.91l-96,56a8,8,0,0,1-8.06,0l-96-56A8,8,0,0,1,36,169.09l92,53.65,92-53.65A8,8,0,0,1,230.91,172ZM220,121.09l-92,53.65L36,121.09A8,8,0,0,0,28,134.91l96,56a8,8,0,0,0,8.06,0l96-56A8,8,0,1,0,220,121.09ZM24,80a8,8,0,0,1,4-6.91l96-56a8,8,0,0,1,8.06,0l96,56a8,8,0,0,1,0,13.82l-96,56a8,8,0,0,1-8.06,0l-96-56A8,8,0,0,1,24,80Zm23.88,0L128,126.74,208.12,80,128,33.26Z",
    graph: "M200,152a31.84,31.84,0,0,0-19.53,6.68l-23.11-18A31.65,31.65,0,0,0,160,128c0-.74,0-1.48-.08-2.21l13.23-4.41A32,32,0,1,0,168,104c0,.74,0,1.48.08,2.21l-13.23,4.41A32,32,0,0,0,128,96a32.59,32.59,0,0,0-5.27.44L115.89,81A32,32,0,1,0,96,88a32.59,32.59,0,0,0,5.27-.44l6.84,15.4a31.92,31.92,0,0,0-8.57,39.64L73.83,165.44a32.06,32.06,0,1,0,10.63,12l25.71-22.84a31.91,31.91,0,0,0,37.36-1.24l23.11,18A31.65,31.65,0,0,0,168,184a32,32,0,1,0,32-32Zm0-64a16,16,0,1,1-16,16A16,16,0,0,1,200,88ZM80,56A16,16,0,1,1,96,72,16,16,0,0,1,80,56ZM56,208a16,16,0,1,1,16-16A16,16,0,0,1,56,208Zm56-80a16,16,0,1,1,16,16A16,16,0,0,1,112,128Zm88,72a16,16,0,1,1,16-16A16,16,0,0,1,200,200Z",
    plus: "M224,128a8,8,0,0,1-8,8H136v80a8,8,0,0,1-16,0V136H40a8,8,0,0,1,0-16h80V40a8,8,0,0,1,16,0v80h80A8,8,0,0,1,224,128Z",
    close: "M205.66,194.34a8,8,0,0,1-11.32,11.32L128,139.31,61.66,205.66a8,8,0,0,1-11.32-11.32L116.69,128,50.34,61.66A8,8,0,0,1,61.66,50.34L128,116.69l66.34-66.35a8,8,0,0,1,11.32,11.32L139.31,128Z",
    download: "M224,144v64a8,8,0,0,1-8,8H40a8,8,0,0,1-8-8V144a8,8,0,0,1,16,0v56H208V144a8,8,0,0,1,16,0Zm-101.66,5.66a8,8,0,0,0,11.32,0l40-40a8,8,0,0,0-11.32-11.32L136,124.69V32a8,8,0,0,0-16,0v92.69L93.66,98.34a8,8,0,0,0-11.32,11.32Z",
    caret: "M213.66,101.66l-80,80a8,8,0,0,1-11.32,0l-80-80A8,8,0,0,1,53.66,90.34L128,164.69l74.34-74.35a8,8,0,0,1,11.32,11.32Z",
    book: "M232,48H160a40,40,0,0,0-32,16A40,40,0,0,0,96,48H24a8,8,0,0,0-8,8V200a8,8,0,0,0,8,8H96a24,24,0,0,1,24,24,8,8,0,0,0,16,0,24,24,0,0,1,24-24h72a8,8,0,0,0,8-8V56A8,8,0,0,0,232,48ZM96,192H32V64H96a24,24,0,0,1,24,24V200A39.81,39.81,0,0,0,96,192Zm128,0H160a39.81,39.81,0,0,0-24,8V88a24,24,0,0,1,24-24h64ZM160,88h40a8,8,0,0,1,0,16H160a8,8,0,0,1,0-16Zm48,40a8,8,0,0,1-8,8H160a8,8,0,0,1,0-16h40A8,8,0,0,1,208,128Zm0,32a8,8,0,0,1-8,8H160a8,8,0,0,1,0-16h40A8,8,0,0,1,208,160Z",
    pin: "M235.32,81.37,174.63,20.69a16,16,0,0,0-22.63,0L98.37,74.49c-10.66-3.34-35-7.37-60.4,13.14a16,16,0,0,0-1.29,23.78L85,159.71,42.34,202.34a8,8,0,0,0,11.32,11.32L96.29,171l48.29,48.29A16,16,0,0,0,155.9,224c.38,0,.75,0,1.13,0a15.93,15.93,0,0,0,11.64-6.33c19.64-26.1,17.75-47.32,13.19-60L235.33,104A16,16,0,0,0,235.32,81.37ZM224,92.69h0l-57.27,57.46a8,8,0,0,0-1.49,9.22c9.46,18.93-1.8,38.59-9.34,48.62L48,100.08c12.08-9.74,23.64-12.31,32.48-12.31A40.13,40.13,0,0,1,96.81,91a8,8,0,0,0,9.25-1.51L163.32,32,224,92.68Z",
    copy: "M216,32H88a8,8,0,0,0-8,8V80H40a8,8,0,0,0-8,8V216a8,8,0,0,0,8,8H168a8,8,0,0,0,8-8V176h40a8,8,0,0,0,8-8V40A8,8,0,0,0,216,32ZM160,208H48V96H160Zm48-48H176V88a8,8,0,0,0-8-8H96V48H208Z"
  };

  const icon = (name, className = "") => `<svg class="icon ${className}" viewBox="0 0 256 256" aria-hidden="true"><path d="${iconPaths[name] || iconPaths.fileMd}"></path></svg>`;
  const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[char]));
  const documentContent = data.document_content && typeof data.document_content === "object" ? data.document_content : {};
  const contentForPath = (path) => {
    const value = documentContent[String(path || "")];
    return value && typeof value === "object" && typeof value.text === "string" ? value : null;
  };
  const stripFrontmatter = (value) => {
    const text = String(value || "").replace(/\r\n?/g, "\n");
    if (!text.startsWith("---\n")) return text;
    const end = text.indexOf("\n---\n", 4);
    return end === -1 ? text : text.slice(end + 5);
  };
  const safeLinkHref = (value) => {
    const href = String(value || "").trim();
    return /^(https?:\/\/|\.\.?\/|#)/i.test(href) ? href : "";
  };
  const renderInlineMarkdown = (value) => {
    const tokens = [];
    const token = (html) => {
      const id = `MIRRORARCTOKEN${tokens.length}END`;
      tokens.push(html);
      return id;
    };
    let work = String(value || "");
    work = work.replace(/`([^`]+)`/g, (_match, code) => token(`<code>${escapeHtml(code)}</code>`));
    work = work.replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g, (_match, target, label) => token(`<button type="button" class="wiki-link" data-wiki-target="${escapeHtml(target.trim())}">${escapeHtml((label || target).trim())}</button>`));
    work = work.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (_match, label, hrefValue) => {
      const href = safeLinkHref(hrefValue);
      return href ? token(`<a href="${escapeHtml(href)}">${escapeHtml(label)}</a>`) : `${label} (${hrefValue})`;
    });
    let html = escapeHtml(work)
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/__([^_]+)__/g, "<strong>$1</strong>")
      .replace(/(^|\s)\*([^*]+)\*(?=\s|$|[.,;:!?])/g, "$1<em>$2</em>");
    html = html.replace(/MIRRORARCTOKEN(\d+)END/g, (_match, index) => tokens[Number(index)] || "");
    return html;
  };
  const renderMarkdown = (value) => {
    const lines = stripFrontmatter(value).split("\n");
    const out = [];
    let paragraph = [];
    let listType = "";
    let inCode = false;
    let codeLines = [];
    const flushParagraph = () => {
      if (!paragraph.length) return;
      out.push(`<p>${renderInlineMarkdown(paragraph.join(" "))}</p>`);
      paragraph = [];
    };
    const closeList = () => {
      if (!listType) return;
      out.push(`</${listType}>`);
      listType = "";
    };
    for (let index = 0; index < lines.length; index += 1) {
      const line = lines[index];
      if (/^```/.test(line)) {
        flushParagraph();
        closeList();
        if (inCode) {
          out.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
          codeLines = [];
        }
        inCode = !inCode;
        continue;
      }
      if (inCode) {
        codeLines.push(line);
        continue;
      }
      if (!line.trim()) {
        flushParagraph();
        closeList();
        continue;
      }
      const heading = line.match(/^(#{1,4})\s+(.+)$/);
      if (heading) {
        flushParagraph();
        closeList();
        const level = heading[1].length;
        out.push(`<h${level}>${renderInlineMarkdown(heading[2])}</h${level}>`);
        continue;
      }
      if (line.includes("|") && index + 1 < lines.length && /^\s*\|?\s*:?-{3,}/.test(lines[index + 1])) {
        flushParagraph();
        closeList();
        const cells = (row) => row.trim().replace(/^\||\|$/g, "").split("|").map((cell) => cell.trim());
        const header = cells(line);
        index += 2;
        const rows = [];
        while (index < lines.length && lines[index].includes("|") && lines[index].trim()) {
          rows.push(cells(lines[index]));
          index += 1;
        }
        index -= 1;
        out.push(`<table><thead><tr>${header.map((cell) => `<th>${renderInlineMarkdown(cell)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${row.map((cell) => `<td>${renderInlineMarkdown(cell)}</td>`).join("")}</tr>`).join("")}</tbody></table>`);
        continue;
      }
      const bullet = line.match(/^\s*[-*+]\s+(.+)$/);
      const ordered = line.match(/^\s*\d+[.)]\s+(.+)$/);
      if (bullet || ordered) {
        flushParagraph();
        const nextType = ordered ? "ol" : "ul";
        if (listType && listType !== nextType) closeList();
        if (!listType) {
          listType = nextType;
          out.push(`<${listType}>`);
        }
        out.push(`<li>${renderInlineMarkdown((bullet || ordered)[1])}</li>`);
        continue;
      }
      if (/^>\s?/.test(line)) {
        flushParagraph();
        closeList();
        const quoteLines = [line.replace(/^>\s?/, "").trim()];
        while (index + 1 < lines.length && lines[index + 1].trim()) {
          const nextLine = lines[index + 1];
          if (/^(#{1,4})\s+|^```|^\s*[-*+]\s+|^\s*\d+[.)]\s+/.test(nextLine)) break;
          index += 1;
          quoteLines.push(nextLine.replace(/^>\s?/, "").trim());
        }
        out.push(`<blockquote>${renderInlineMarkdown(quoteLines.join(" "))}</blockquote>`);
        continue;
      }
      if (/^\s*([-*_])(?:\s*\1){2,}\s*$/.test(line)) {
        flushParagraph();
        closeList();
        out.push("<hr>");
        continue;
      }
      paragraph.push(line.trim());
    }
    if (inCode && codeLines.length) out.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
    flushParagraph();
    closeList();
    return out.join("");
  };
  const labelForPath = (path) => {
    const name = String(path || "Untitled").split("/").pop() || "Untitled";
    return name.replace(/\.mirror\.md$/i, ".mirror.md");
  };
  const hrefForPath = (path) => "./" + String(path || "").split("/").map(encodeURIComponent).join("/");
  const normalizeState = (value) => String(value || "unknown").toLowerCase().replace(/_/g, " ");
  const isHealthy = (node) => !node.attention;
  const kindLabel = {
    source: "Original source",
    unmanaged: "Unmanaged source",
    mirror: "Generated mirror",
    curated: "Authoritative Markdown",
    machine: "Machine-owned note",
    repo: "Repository",
    "repo-note": "Repository mirror",
    code: "Code evidence",
    domain: "Profile domain",
    review: "Lifecycle review",
    pack: "Context pack"
    ,view: "Knowledge view"
    ,profile: "Profile contract"
  };
  const kindIcon = {
    source: "fileDoc",
    unmanaged: "fileDoc",
    mirror: "fileMd",
    curated: "fileMd",
    machine: "fileMd",
    repo: "graph",
    "repo-note": "fileMd",
    code: "graph",
    domain: "folder",
    review: "pin",
    pack: "stack"
    ,view: "book"
    ,profile: "folder"
  };

  const nodes = [];
  const nodeById = new Map();
  const pathToNode = new Map();
  const baseEdges = [];
  const addNode = (node) => {
    if (!node || !node.id || nodeById.has(node.id)) return nodeById.get(node.id);
    const complete = {
      path: "",
      title: "Untitled",
      subtitle: kindLabel[node.kind] || "Evidence",
      domain: "unclassified",
      state: "unknown",
      warnings: 0,
      errors: 0,
      attention: false,
      ...node
    };
    nodes.push(complete);
    nodeById.set(complete.id, complete);
    if (complete.path && !pathToNode.has(complete.path)) pathToNode.set(complete.path, complete.id);
    return complete;
  };
  const addEdge = (source, target, relation, details = {}) => {
    if (!source || !target || source === target) return;
    const key = `${source}|${target}|${relation}`;
    const existing = baseEdges.find((edge) => edge.key === key || (edge.relation === relation && edge.source === target && edge.target === source));
    if (existing) {
      if (Array.isArray(details.evidence) && details.evidence.length) existing.evidence = details.evidence;
      existing.relationshipState = details.state || existing.relationshipState;
      existing.relationshipId = details.relationship_id || existing.relationshipId;
      existing.relationshipMethod = details.method || existing.relationshipMethod;
      existing.relationshipReviews = details.reviews || existing.relationshipReviews;
      existing.invalidationReason = details.invalidation_reason || existing.invalidationReason;
      return;
    }
    baseEdges.push({
      key, source, target, relation,
      evidence: details.evidence || [],
      relationshipState: details.state || "accepted",
      relationshipId: details.relationship_id || "",
      relationshipMethod: details.method || "deterministic",
      relationshipReviews: details.reviews || [],
      invalidationReason: details.invalidation_reason || ""
    });
  };

  const domains = Array.isArray(data.domains) ? data.domains : [];
  domains.forEach((item) => addNode({
    id: `domain:${item.domain}`,
    kind: "domain",
    title: item.folder || item.domain,
    subtitle: item.domain,
    domain: item.domain,
    state: "profile",
    purpose: item.purpose || "Profile-defined knowledge domain."
  }));
  if (!nodeById.has("domain:unclassified")) addNode({
    id: "domain:unclassified",
    kind: "domain",
    title: "Unclassified",
    subtitle: "Needs profile routing",
    domain: "unclassified",
    state: "attention",
    attention: true,
    purpose: "Evidence outside a configured profile domain."
  });

  (data.source_items || []).forEach((item, index) => {
    const stable = item.source_id || `${item.source || "source"}-${index}`;
    const sourceId = `source:${stable}`;
    const mirrorId = `mirror:${stable}`;
    const attention = Boolean(item.warnings || item.errors || !["clean", "active", "reviewed", "regenerated"].includes(String(item.state || "").toLowerCase()));
    addNode({
      id: sourceId,
      kind: "source",
      title: labelForPath(item.source),
      subtitle: "Original document",
      path: item.source,
      domain: item.domain || "unclassified",
      state: item.state,
      warnings: item.warnings || 0,
      errors: item.errors || 0,
      attention,
      sourceId: item.source_id,
      format: item.format,
      sourceSha256: item.source_sha256,
      lastMaterialized: item.last_successful_sync,
      lifecycleContract: item.lifecycle_contract,
      lifecycleSchema: item.lifecycle_contract_schema_version,
      authoritativePath: item.source,
      provenance: [item.source]
      ,layer: "L0"
      ,authority: "authoritative"
    });
    if (item.mirror) {
      addNode({
        id: mirrorId,
        kind: "mirror",
        title: labelForPath(item.mirror),
        subtitle: "Generated mirror",
        path: item.mirror,
        domain: item.domain || "unclassified",
        state: item.state,
        warnings: item.warnings || 0,
        errors: item.errors || 0,
        attention,
        sourceId: item.source_id,
        format: "md",
        sourceSha256: item.source_sha256,
        lastMaterialized: item.last_successful_sync,
        lifecycleContract: item.lifecycle_contract,
        lifecycleSchema: item.lifecycle_contract_schema_version,
        authoritativePath: item.source,
        provenance: [item.source, item.mirror]
        ,layer: "L1"
        ,authority: "derived"
      });
      addEdge(sourceId, mirrorId, "MIRRORS");
      addEdge(mirrorId, `domain:${item.domain || "unclassified"}`, "IN_DOMAIN");
      const reviewId = `review:${stable}`;
      addNode({
        id: reviewId,
        kind: "review",
        title: attention ? "Review attention" : "Lifecycle current",
        subtitle: normalizeState(item.state),
        domain: item.domain || "unclassified",
        state: attention ? "attention" : "current",
        attention,
        authoritativePath: item.source,
        provenance: [item.source, item.mirror]
      });
      addEdge(mirrorId, reviewId, "LIFECYCLE");
    } else {
      addEdge(sourceId, `domain:${item.domain || "unclassified"}`, "IN_DOMAIN");
    }
  });

  (data.curated_items || []).forEach((item, index) => {
    const id = `note:${item.path || index}`;
    addNode({
      id,
      kind: "curated",
      title: item.title || labelForPath(item.path),
      subtitle: item.note_type || "Governed Markdown record",
      path: item.path,
      domain: item.domain || "unclassified",
      state: item.status || "curated",
      noteType: item.note_type,
      authoritativePath: item.path,
      provenance: [item.path]
      ,layer: "L0"
      ,authority: "authoritative"
    });
    addEdge(id, `domain:${item.domain || "unclassified"}`, "IN_DOMAIN");
  });

  (data.machine_owned_items || []).forEach((item, index) => {
    if (pathToNode.has(item.path)) return;
    const id = `machine:${item.path || index}`;
    addNode({
      id,
      kind: "machine",
      title: item.title || labelForPath(item.path),
      subtitle: item.note_type || "Machine-owned note",
      path: item.path,
      domain: item.domain || "unclassified",
      state: item.status || "generated",
      authoritativePath: item.path,
      provenance: [item.path]
      ,layer: "control"
      ,authority: "operational"
    });
    addEdge(id, `domain:${item.domain || "unclassified"}`, "IN_DOMAIN");
  });

  const codeByRepo = new Map((codeData.repositories || []).map((item) => [item.repo_id, item]));
  (data.repo_items || []).forEach((item, index) => {
    const stable = item.repo_id || `${item.repo || "repo"}-${index}`;
    const repoId = `repo:${stable}`;
    const noteId = `repo-note:${stable}`;
    const attention = Boolean(item.warnings || item.errors || !["clean", "active", "reviewed"].includes(String(item.state || "").toLowerCase()));
    const domain = item.domain || "sources";
    const codeRecord = codeByRepo.get(item.repo_id) || null;
    addNode({
      id: repoId,
      kind: "repo",
      title: item.repo || "Repository",
      subtitle: "Original repository",
      domain,
      state: item.state,
      warnings: item.warnings || 0,
      errors: item.errors || 0,
      attention,
      sourceId: item.repo_id,
      commit: item.commit,
      lastMaterialized: item.last_successful_sync,
      lifecycleContract: item.lifecycle_contract,
      lifecycleSchema: item.lifecycle_contract_schema_version,
      authoritativePath: item.repo,
      provenance: [item.repo]
      ,codeRecord
      ,layer: "L0"
      ,authority: "authoritative"
    });
    if (item.note) {
      addNode({
        id: noteId,
        kind: "repo-note",
        title: labelForPath(item.note),
        subtitle: "Repository mirror",
        path: item.note,
        domain,
        state: item.state,
        warnings: item.warnings || 0,
        errors: item.errors || 0,
        attention,
        sourceId: item.repo_id,
        commit: item.commit,
        lastMaterialized: item.last_successful_sync,
        lifecycleContract: item.lifecycle_contract,
        lifecycleSchema: item.lifecycle_contract_schema_version,
        authoritativePath: item.repo,
        provenance: [item.repo, item.note]
        ,codeRecord
        ,layer: "L1"
        ,authority: "derived"
      });
      addEdge(repoId, noteId, "MIRRORS");
      addEdge(noteId, `domain:${domain}`, "IN_DOMAIN");
    }
  });

  (data.unmanaged_sources || []).forEach((path, index) => {
    if (pathToNode.has(path)) return;
    const id = `unmanaged:${path || index}`;
    addNode({
      id,
      kind: "unmanaged",
      title: labelForPath(path),
      subtitle: "Unmanaged source",
      path,
      domain: "unclassified",
      state: "needs planning",
      attention: true,
      authoritativePath: path,
      provenance: [path]
      ,layer: "L0"
      ,authority: "authoritative"
    });
    addEdge(id, "domain:unclassified", "NEEDS_ROUTING");
  });

  const artifactToNode = new Map();
  const kindForArtifact = (kind, layer) => {
    if (kind === "projection") return "mirror";
    if (kind === "native-source") return "curated";
    if (kind === "repository") return "repo";
    if (kind === "code-evidence") return "code";
    if (kind === "knowledge-view") return "view";
    if (kind === "context") return "pack";
    if (kind === "profile") return "profile";
    if (kind === "domain") return "domain";
    if (kind === "lifecycle") return "review";
    if (kind === "source") return "source";
    return layer === "L2" ? "view" : "machine";
  };
  (projectionData.artifacts || []).forEach((artifact) => {
    if (artifact.artifact_kind === "code-evidence") {
      const current = codeByRepo.get(artifact.metadata?.repo_id) || null;
      if (!current?.analysis || current.analysis.analysis_id !== artifact.artifact_id) return;
    }
    const path = String(artifact.path || "");
    let nodeId = path ? pathToNode.get(path) : "";
    if (!nodeId && artifact.artifact_kind === "repository" && nodeById.has(`repo:${artifact.artifact_id}`)) nodeId = `repo:${artifact.artifact_id}`;
    if (!nodeId && artifact.artifact_kind === "domain") nodeId = nodeById.has(`domain:${artifact.title}`) ? `domain:${artifact.title}` : "";
    if (!nodeId) {
      const kind = kindForArtifact(artifact.artifact_kind, artifact.layer);
      nodeId = `artifact:${artifact.artifact_id}`;
      addNode({
        id: nodeId,
        kind,
        title: artifact.title || labelForPath(path) || artifact.artifact_id,
        subtitle: `${artifact.layer || "evidence"} · ${artifact.artifact_kind || "artifact"}`,
        path,
        domain: artifact.domain || (kind === "profile" ? "profile" : "unclassified"),
        state: artifact.lifecycle_state || "current",
        attention: ["stale", "failed", "source_missing", "invalidated"].includes(String(artifact.lifecycle_state || "").toLowerCase()),
        sourceId: artifact.artifact_id,
        sourceSha256: artifact.content_hash,
        authoritativePath: path,
        provenance: path ? [path] : [],
        layer: artifact.layer || "evidence",
        authority: artifact.authority || "derived",
        artifactKind: artifact.artifact_kind,
        artifactMetadata: artifact.metadata || {}
      });
    } else {
      const node = nodeById.get(nodeId);
      node.sourceId = artifact.artifact_id;
      node.sourceSha256 = artifact.content_hash || node.sourceSha256;
      node.layer = artifact.layer || node.layer;
      node.authority = artifact.authority || node.authority;
      node.artifactKind = artifact.artifact_kind;
      node.artifactMetadata = artifact.metadata || {};
      node.state = artifact.lifecycle_state || node.state;
      if (artifact.artifact_kind === "code-evidence") node.codeRecord = codeByRepo.get(artifact.metadata?.repo_id) || null;
    }
    if (artifact.artifact_kind === "code-evidence") {
      const node = nodeById.get(nodeId);
      const codeRecord = codeByRepo.get(artifact.metadata?.repo_id) || null;
      node.codeRecord = codeRecord;
      node.state = codeRecord?.freshness_state || node.state;
      node.attention = ["stale", "failed", "no-analysis"].includes(String(node.state || "").toLowerCase());
      node.warnings = Number(codeRecord?.analysis?.warnings?.length || 0);
      node.errors = node.state === "failed" ? 1 : 0;
    }
    artifactToNode.set(artifact.artifact_id, nodeId);
  });
  (projectionData.relationships || []).forEach((relationship) => {
    addEdge(
      artifactToNode.get(relationship.source_artifact_id),
      artifactToNode.get(relationship.target_artifact_id),
      relationship.relationship_type,
      relationship
    );
  });

  const packNode = addNode({
    id: "pack:review",
    kind: "pack",
    title: "Review context pack",
    subtitle: "Metadata-only export",
    domain: "context",
    state: "local",
    purpose: "A bounded local export of selected paths and evidence metadata."
  });

  const state = {
    selectedId: pathToNode.get("INDEX.md") || (nodes.find((node) => node.kind === "mirror") || nodes.find((node) => !["domain", "review", "pack"].includes(node.kind)) || nodes[0] || packNode).id,
    view: "content",
    hops: 2,
    sidebarTab: "browse",
    search: "",
    filters: new Set(),
    context: new Set(),
    scale: 0.8,
    manualScale: false,
    graphWidth: 760,
    graphHeight: 720,
    catalogWidth: 280,
    collapsed: new Set(["L1"]),
    relationshipFilter: ""
  };

  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => Array.from(document.querySelectorAll(selector));
  const leftPanel = $("#left-panel");
  const rightPanel = $("#right-panel");
  const mobileBackdrop = $("#mobile-backdrop");
  const graphViewport = $("#graph-viewport");
  const graphStage = $("#graph-stage");
  const graphStageSpace = $("#graph-stage-space");
  const collectionScroll = $("#collection-scroll");
  const pinnedIndex = $("#pinned-index");
  const leftResizer = $("#left-resizer");
  const inspectorScroll = $("#inspector-scroll");
  const metadataView = $("#metadata-view");
  const documentView = $("#document-view");
  const codeView = $("#code-view");
  const mapView = $("#map-view");

  const currentEdges = () => {
    const edges = baseEdges.slice();
    state.context.forEach((id) => edges.push({key: `${id}|pack:review|IN_CONTEXT`, source: id, target: "pack:review", relation: "IN_CONTEXT"}));
    return edges;
  };

  const relatedFor = (id) => currentEdges().filter((edge) => edge.source === id || edge.target === id).map((edge) => ({
    edge,
    node: nodeById.get(edge.source === id ? edge.target : edge.source)
  })).filter((item) => item.node);

  const visibleGraph = () => {
    if (!nodeById.has(state.selectedId)) return {nodes: [], edges: []};
    const edges = currentEdges();
    const adjacency = new Map();
    edges.forEach((edge) => {
      if (!adjacency.has(edge.source)) adjacency.set(edge.source, []);
      if (!adjacency.has(edge.target)) adjacency.set(edge.target, []);
      adjacency.get(edge.source).push(edge.target);
      adjacency.get(edge.target).push(edge.source);
    });
    const distance = new Map([[state.selectedId, 0]]);
    const queue = [state.selectedId];
    while (queue.length) {
      const id = queue.shift();
      const depth = distance.get(id);
      if (depth >= state.hops) continue;
      (adjacency.get(id) || []).forEach((next) => {
        if (!distance.has(next)) {
          distance.set(next, depth + 1);
          queue.push(next);
        }
      });
    }
    let visibleNodes = Array.from(distance.keys()).map((id) => nodeById.get(id)).filter(Boolean);
    if (visibleNodes.length > 18) visibleNodes = visibleNodes.slice(0, 18);
    const ids = new Set(visibleNodes.map((node) => node.id));
    const visibleEdges = edges.filter((edge) => ids.has(edge.source) && ids.has(edge.target));
    return {nodes: visibleNodes, edges: visibleEdges};
  };

  const rankFor = (node) => ({source: 0, unmanaged: 0, repo: 0, mirror: 1, "repo-note": 1, code: 2, curated: 2, machine: 2, view: 3, domain: 4, profile: 4, review: 5, pack: 6}[node.kind] ?? 2);
  const NODE_WIDTH = 214;
  const NODE_HEIGHT = 88;
  const NODE_GAP = 46;
  const COLUMN_STEP = 330;
  const layoutGraph = (graph) => {
    const columns = new Map();
    graph.nodes.forEach((node) => {
      const rank = rankFor(node);
      if (!columns.has(rank)) columns.set(rank, []);
      columns.get(rank).push(node);
    });
    columns.forEach((column) => {
      column.sort((a, b) => a.title.localeCompare(b.title));
      const selectedIndex = column.findIndex((node) => node.id === state.selectedId);
      if (selectedIndex >= 0 && column.length > 1) {
        const [selected] = column.splice(selectedIndex, 1);
        column.splice(Math.floor(column.length / 2), 0, selected);
      }
    });
    const maxColumnSize = Math.max(1, ...Array.from(columns.values()).map((column) => column.length));
    state.graphHeight = Math.max(720, 156 + maxColumnSize * NODE_HEIGHT + Math.max(0, maxColumnSize - 1) * NODE_GAP);
    const positions = new Map();
    columns.forEach((column, rank) => {
      const columnHeight = column.length * NODE_HEIGHT + Math.max(0, column.length - 1) * NODE_GAP;
      const startY = Math.max(92, (state.graphHeight - columnHeight) / 2);
      column.forEach((node, index) => positions.set(node.id, {x: 40 + rank * COLUMN_STEP, y: startY + index * (NODE_HEIGHT + NODE_GAP), rank}));
    });
    return {positions, columns};
  };

  const renderGraph = () => {
    const graph = visibleGraph();
    const {positions, columns} = layoutGraph(graph);
    const maxRank = columns.size ? Math.max(...columns.keys()) : 0;
    state.graphWidth = Math.max(800, 80 + maxRank * COLUMN_STEP + NODE_WIDTH + 40);
    graphStage.style.width = `${state.graphWidth}px`;
    graphStage.style.height = `${state.graphHeight}px`;
    graphStage.replaceChildren();

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("class", "edge-layer");
    svg.setAttribute("viewBox", `0 0 ${state.graphWidth} ${state.graphHeight}`);
    svg.innerHTML = `<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#7e91a3"></path></marker><marker id="arrow-focus" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#008f83"></path></marker></defs>`;

    const edgeLayouts = graph.edges.map((edge, index) => ({edge, index, from: positions.get(edge.source), to: positions.get(edge.target)})).filter((item) => item.from && item.to);
    const sideGroups = new Map();
    const registerSide = (key, item, otherY) => {
      if (!sideGroups.has(key)) sideGroups.set(key, []);
      sideGroups.get(key).push({item, otherY});
    };
    edgeLayouts.forEach((item) => {
      const forward = item.to.x >= item.from.x;
      registerSide(`${item.edge.source}:${forward ? "right" : "left"}`, item, item.to.y);
      registerSide(`${item.edge.target}:${forward ? "left" : "right"}`, item, item.from.y);
    });
    sideGroups.forEach((items) => items.sort((a, b) => a.otherY - b.otherY));
    const portY = (nodeId, side, item, position) => {
      const items = sideGroups.get(`${nodeId}:${side}`) || [];
      const index = Math.max(0, items.findIndex((entry) => entry.item === item));
      const spacing = Math.min(10, (NODE_HEIGHT - 24) / Math.max(items.length - 1, 1));
      return position.y + NODE_HEIGHT / 2 + (index - (items.length - 1) / 2) * spacing;
    };
    const laneGroups = new Map();
    edgeLayouts.forEach((item) => {
      const key = `${Math.min(item.from.rank, item.to.rank)}:${Math.max(item.from.rank, item.to.rank)}`;
      if (!laneGroups.has(key)) laneGroups.set(key, []);
      laneGroups.get(key).push(item);
    });
    laneGroups.forEach((items) => items.sort((a, b) => (a.from.y + a.to.y) - (b.from.y + b.to.y)));
    const longEdges = edgeLayouts.filter((item) => Math.abs(item.from.rank - item.to.rank) > 1);
    const relationLabels = new Set();
    edgeLayouts.forEach((item) => {
      const {edge, from, to} = item;
      const forward = to.x >= from.x;
      const sourceSide = forward ? "right" : "left";
      const targetSide = forward ? "left" : "right";
      const x1 = from.x + (forward ? NODE_WIDTH : 0);
      const y1 = portY(edge.source, sourceSide, item, from);
      const x2 = to.x + (forward ? 0 : NODE_WIDTH);
      const y2 = portY(edge.target, targetSide, item, to);
      const laneKey = `${Math.min(from.rank, to.rank)}:${Math.max(from.rank, to.rank)}`;
      const laneItems = laneGroups.get(laneKey) || [item];
      const laneIndex = laneItems.indexOf(item);
      const laneStep = Math.min(14, Math.max(8, Math.abs(x2 - x1) / Math.max(laneItems.length + 2, 3)));
      const laneX = (x1 + x2) / 2 + (laneIndex - (laneItems.length - 1) / 2) * laneStep;
      const longEdgeIndex = longEdges.indexOf(item);
      const isLongEdge = longEdgeIndex >= 0;
      const corridorOffset = Math.floor(longEdgeIndex / 2) * 14;
      const corridorY = longEdgeIndex % 2 === 0 ? 50 + corridorOffset : state.graphHeight - 50 - corridorOffset;
      const sourceStubX = x1 + (forward ? 36 : -36);
      const targetStubX = x2 + (forward ? -36 : 36);
      const pathData = isLongEdge
        ? `M ${x1} ${y1} H ${sourceStubX} V ${corridorY} H ${targetStubX} V ${y2} H ${x2}`
        : `M ${x1} ${y1} H ${laneX} V ${y2} H ${x2}`;
      const focused = edge.source === state.selectedId || edge.target === state.selectedId;
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("class", `edge-path${focused ? " is-focus" : ""}`);
      path.setAttribute("d", pathData);
      path.setAttribute("marker-end", focused ? "url(#arrow-focus)" : "url(#arrow)");
      path.dataset.source = edge.source;
      path.dataset.target = edge.target;
      svg.appendChild(path);
      if (focused && !relationLabels.has(edge.relation)) {
        relationLabels.add(edge.relation);
        const labelWidth = Math.max(54, edge.relation.length * 6.2 + 14);
        const labelCenterX = isLongEdge ? (sourceStubX + targetStubX) / 2 : (x1 + laneX) / 2;
        const labelX = labelCenterX - labelWidth / 2;
        const labelY = (isLongEdge ? corridorY : y1) - 22;
        const labelGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
        labelGroup.setAttribute("class", "edge-label-group");
        labelGroup.innerHTML = `<rect class="edge-label-bg" x="${labelX}" y="${labelY}" width="${labelWidth}" height="18" rx="4"></rect><text class="edge-label" x="${labelX + labelWidth / 2}" y="${labelY + 12.5}" text-anchor="middle">${escapeHtml(edge.relation)}</text>`;
        svg.appendChild(labelGroup);
      }
    });
    graphStage.appendChild(svg);

    const groupLabels = {0: "L0 sources", 1: "L1 projections", 2: "Governed records", 3: "L2 views", 4: "Profile", 5: "Review", 6: "Context"};
    const groupClasses = {0: "domain-source", 1: "domain-mirror", 2: "domain-curated", 3: "domain-curated", 4: "domain-governance", 5: "domain-curated", 6: "domain-governance"};
    columns.forEach((column, rank) => {
      const coords = column.map((node) => positions.get(node.id));
      const minY = Math.min(...coords.map((pos) => pos.y)) - 46;
      const maxY = Math.max(...coords.map((pos) => pos.y)) + NODE_HEIGHT + 22;
      const group = document.createElement("div");
      group.className = `graph-group ${groupClasses[rank] || ""}`;
      group.style.left = `${coords[0].x - 12}px`;
      group.style.top = `${Math.max(30, minY)}px`;
      group.style.width = `${NODE_WIDTH + 24}px`;
      group.style.height = `${Math.max(132, maxY - Math.max(30, minY))}px`;
      group.innerHTML = `<span class="graph-group-label">${escapeHtml(groupLabels[rank] || "Evidence")}</span>`;
      graphStage.appendChild(group);
    });

    graph.nodes.forEach((node, index) => {
      const pos = positions.get(node.id);
      const button = document.createElement("button");
      button.type = "button";
      button.className = `entity-card kind-${node.kind}${node.id === state.selectedId ? " selected" : ""}${node.attention ? " attention" : ""}`;
      button.style.left = `${pos.x}px`;
      button.style.top = `${pos.y}px`;
      button.style.animationDelay = `${Math.min(index * 22, 220)}ms`;
      button.dataset.nodeId = node.id;
      button.setAttribute("aria-label", `${node.title}, ${kindLabel[node.kind] || "evidence"}`);
      button.title = node.title;
      button.innerHTML = `${icon(kindIcon[node.kind] || "fileMd", "large node-icon")}<span class="node-copy"><span class="node-title">${escapeHtml(node.title)}</span><span class="node-subtitle">${escapeHtml(node.subtitle)}</span></span>${icon(node.attention ? "warning" : "check", "small node-status")}`;
      button.addEventListener("click", () => selectNode(node.id));
      button.addEventListener("mouseenter", () => svg.querySelectorAll(".edge-path").forEach((path) => path.classList.toggle("is-hover", path.dataset.source === node.id || path.dataset.target === node.id)));
      button.addEventListener("mouseleave", () => svg.querySelectorAll(".edge-path").forEach((path) => path.classList.remove("is-hover")));
      graphStage.appendChild(button);
    });

    if (!graph.nodes.length) {
      const empty = document.createElement("div");
      empty.className = "graph-empty";
      empty.innerHTML = `${icon("graph", "large")}<p>No catalog evidence is available yet. Run a sync, then regenerate this catalog.</p>`;
      graphStage.appendChild(empty);
    }
    applyScale();
    const hidden = Math.max(0, nodes.length - graph.nodes.length);
    $("#hidden-node-count").textContent = String(hidden + Number(data.hidden_counts?.total || 0));
  };

  const indexNodeId = pathToNode.get("INDEX.md");
  const sidebarNodes = () => nodes.filter((node) => !["domain", "review", "pack", "profile"].includes(node.kind) && node.id !== indexNodeId);
  const matchesFilters = (node) => {
    if (state.relationshipFilter && !currentEdges().some((edge) => edge.relation === state.relationshipFilter && (edge.source === node.id || edge.target === node.id))) return false;
    if (!state.filters.size) return true;
    if (state.filters.has("attention") && node.attention) return true;
    if (state.filters.has("healthy") && !node.attention) return true;
    if (state.filters.has("sources") && ["source", "unmanaged", "repo"].includes(node.kind)) return true;
    if (state.filters.has("notes") && ["mirror", "curated", "machine", "repo-note", "code", "view"].includes(node.kind)) return true;
    if (state.filters.has("l0") && node.layer === "L0") return true;
    if (state.filters.has("l1") && node.layer === "L1") return true;
    if (state.filters.has("l2") && node.layer === "L2") return true;
    if (state.filters.has("stale") && normalizeState(node.state).includes("stale")) return true;
    if (state.filters.has("reviewed") && normalizeState(node.state).includes("reviewed")) return true;
    return false;
  };
  const renderPinnedIndex = () => {
    if (!pinnedIndex) return;
    const indexNode = indexNodeId ? nodeById.get(indexNodeId) : null;
    pinnedIndex.replaceChildren();
    if (!indexNode) return;
    const button = document.createElement("button");
    button.type = "button";
    button.className = `index-entry${indexNode.id === state.selectedId ? " selected" : ""}`;
    button.dataset.nodeId = indexNode.id;
    button.setAttribute("aria-label", `Start here: INDEX.md, ${indexNode.title}`);
    button.title = indexNode.title;
    button.innerHTML = `${icon("book", "large")}<span class="index-entry-copy"><span class="index-entry-title">INDEX.md</span><span class="index-entry-subtitle">Five-minute workspace tour</span></span>${icon("caret", "small")}`;
    button.addEventListener("click", () => selectNode(indexNode.id));
    pinnedIndex.innerHTML = `<div class="pinned-index-label">${icon("stack", "small")}Beginner guide</div>`;
    pinnedIndex.appendChild(button);
  };
  const renderSidebar = () => {
    renderPinnedIndex();
    const term = state.search.trim().toLowerCase();
    let items = sidebarNodes().filter((node) => {
      if (state.sidebarTab === "saved" && !state.context.has(node.id)) return false;
      if (term && !`${node.title} ${node.path} ${node.domain} ${node.state}`.toLowerCase().includes(term)) return false;
      return matchesFilters(node);
    });
    const groups = new Map();
    items.forEach((node) => {
      const key = `${node.domain || "unclassified"}|${node.layer || "unlayered"}`;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(node);
    });
    collectionScroll.replaceChildren();
    if (!items.length) {
      const empty = document.createElement("div");
      empty.className = "sidebar-empty";
      empty.textContent = state.sidebarTab === "saved" ? "No evidence has been added to this context pack." : "No catalog items match this view.";
      collectionScroll.appendChild(empty);
      return;
    }
    Array.from(groups.entries()).sort(([a], [b]) => a.localeCompare(b)).forEach(([groupKey, groupItems]) => {
      const [domain, layer] = groupKey.split("|");
      const section = document.createElement("section");
      section.className = `collection${state.collapsed.has(layer) || state.collapsed.has(groupKey) ? " collapsed" : ""}`;
      const header = document.createElement("button");
      header.type = "button";
      header.className = "collection-header";
      header.setAttribute("aria-expanded", String(!(state.collapsed.has(layer) || state.collapsed.has(groupKey))));
      header.innerHTML = `${icon("caret", "small caret")}${icon("folder", "small")}<span>${escapeHtml(domain)} · ${escapeHtml(layer)}</span><span class="collection-count">${groupItems.length}</span>`;
      header.addEventListener("click", () => {
        if (state.collapsed.has(layer)) state.collapsed.delete(layer);
        else state.collapsed.has(groupKey) ? state.collapsed.delete(groupKey) : state.collapsed.add(groupKey);
        renderSidebar();
      });
      section.appendChild(header);
      const list = document.createElement("div");
      list.className = "collection-items";
      groupItems.sort((a, b) => a.title.localeCompare(b.title)).forEach((node) => {
        const row = document.createElement("button");
        row.type = "button";
        row.className = `entity-row${node.id === state.selectedId ? " selected" : ""}${node.attention ? " attention" : ""}`;
        row.dataset.nodeId = node.id;
        row.title = node.title;
        row.innerHTML = `${icon(kindIcon[node.kind] || "fileMd", "small")}<span class="row-label">${escapeHtml(node.title)}</span>${icon(node.attention ? "warning" : "check", "small status-icon")}`;
        row.addEventListener("click", () => selectNode(node.id));
        list.appendChild(row);
      });
      section.appendChild(list);
      collectionScroll.appendChild(section);
    });
  };

  const provenanceMarkup = (node) => {
    const paths = Array.isArray(node.provenance) && node.provenance.length ? node.provenance : [node.path || node.authoritativePath].filter(Boolean);
    return paths.map((path, index) => {
      const content = node.path && path === node.path ? `<a href="${escapeHtml(hrefForPath(path))}">${escapeHtml(path)}</a>` : escapeHtml(path);
      return index === 0 ? `<div>${content}</div>` : `<span>${content}</span>`;
    }).join("") || "<div>No file path recorded.</div>";
  };

  const renderInspector = () => {
    const node = nodeById.get(state.selectedId) || packNode;
    const related = relatedFor(node.id).slice(0, 8);
    const healthy = isHealthy(node);
    const inContext = state.context.has(node.id);
    const governance = related.map(({edge, node: other}) => {
      const reviews = Array.isArray(edge.relationshipReviews) ? edge.relationshipReviews : [];
      const latest = reviews.length ? reviews[reviews.length - 1] : null;
      const decision = latest
        ? `Reviewed by ${latest.reviewer || "unknown"}: ${latest.verdict || edge.relationshipState}${latest.note ? ` — ${latest.note}` : ""}`
        : edge.relationshipMethod !== "deterministic"
          ? "Awaiting an explicit human review decision."
          : "Deterministic relationship; no semantic review required.";
      const invalidation = edge.invalidationReason ? ` Invalidation: ${edge.invalidationReason}` : "";
      return `<div class="relationship-decision"><div class="relationship-decision-head"><strong>${escapeHtml(`${edge.relation} → ${other.title}`)}</strong><span class="relationship-decision-state">${escapeHtml(edge.relationshipState || "accepted")}</span></div><div class="relationship-decision-meta">${escapeHtml(`${edge.relationshipMethod || "deterministic"}. ${decision}${invalidation}`)}</div></div>`;
    }).join("");
    inspectorScroll.innerHTML = `
      <section class="inspector-identity">
        ${icon(kindIcon[node.kind] || "fileMd", "large identity-icon")}
        <div><div class="identity-title">${escapeHtml(node.title)}</div><div class="identity-subtitle">${escapeHtml(kindLabel[node.kind] || node.subtitle)}</div></div>
        <span class="status-pill${healthy ? "" : " attention"}">${icon(healthy ? "check" : "warning", "small")}${escapeHtml(healthy ? "Current" : "Attention")}</span>
      </section>
      <section class="inspector-section">
        <div class="inspector-section-title">Lifecycle<span class="spacer"></span>${icon(healthy ? "check" : "warning", "small")}<span>${escapeHtml(normalizeState(node.state))}</span></div>
      </section>
      <section class="inspector-section">
        <div class="inspector-section-title">Provenance path</div>
        <div class="inspector-section-body"><div class="provenance-path">${provenanceMarkup(node)}</div></div>
      </section>
      <section class="inspector-section">
        <div class="inspector-section-title">Authoritative source</div>
        <div class="inspector-section-body">
          <div class="inspector-row"><span>Record</span><strong>${escapeHtml(node.authoritativePath || "Profile metadata")}</strong></div>
          <div class="inspector-row"><span>Authority</span><strong>${escapeHtml(["mirror", "repo-note", "machine", "code"].includes(node.kind) ? "Derived projection" : node.kind === "curated" ? "Human governed" : "Original / profile")}</strong></div>
        </div>
      </section>
      <section class="inspector-section">
        <div class="inspector-section-title">Evidence metadata</div>
        <div class="inspector-section-body">
          <div class="inspector-row"><span>Stable ID</span><strong>${escapeHtml(node.sourceId || "not recorded")}</strong></div>
          <div class="inspector-row"><span>Domain</span><strong>${escapeHtml(node.domain || "unclassified")}</strong></div>
          <div class="inspector-row"><span>Layer / type</span><strong>${escapeHtml(`${node.layer || "unlayered"} / ${node.artifactKind || node.kind}`)}</strong></div>
          <div class="inspector-row"><span>Authority</span><strong>${escapeHtml(node.authority || "not recorded")}</strong></div>
          <div class="inspector-row"><span>Format</span><strong>${escapeHtml(node.format || node.noteType || "metadata")}</strong></div>
          <div class="inspector-row"><span>Source hash</span><strong>${escapeHtml(node.sourceSha256 ? `sha256: ${node.sourceSha256.slice(0, 12)}…` : "not recorded")}</strong></div>
          <div class="inspector-row"><span>Last materialized</span><strong>${escapeHtml(node.lastMaterialized || "not recorded")}</strong></div>
          <div class="inspector-row"><span>Warnings / errors</span><strong>${escapeHtml(`${node.warnings || 0} / ${node.errors || 0}`)}</strong></div>
        </div>
      </section>
      <section class="inspector-section">
        <div class="inspector-section-title">Related evidence (${related.length})</div>
        <div class="inspector-section-body"><div class="relationship-list">${related.length ? related.map(({edge, node: other}) => `<button type="button" class="relationship-row" data-related-id="${escapeHtml(other.id)}">${icon(kindIcon[other.kind] || "fileMd", "small")}<span class="rel-title">${escapeHtml(other.title)}</span><span><span class="rel-kind">${escapeHtml(edge.relation)}</span><br><span class="rel-state">${escapeHtml(edge.relationshipState || "accepted")}</span></span></button>`).join("") : `<div class="inspector-row"><span>No direct relationships in this portable catalog.</span></div>`}</div></div>
      </section>
      <section class="inspector-section">
        <div class="inspector-section-title">Relationship governance</div>
        <div class="inspector-section-body"><div class="relationship-governance">${governance || `<div class="inspector-row"><span>No governed relationship decisions are recorded.</span></div>`}</div></div>
      </section>
      <section class="inspector-section">
        <div class="inspector-section-title">Evidence anchors</div>
        <div class="inspector-section-body">${related.flatMap(({edge}) => edge.evidence || []).slice(0, 8).map((anchor) => `<div class="inspector-row"><span>${escapeHtml(anchor.selector_type || "anchor")} · ${escapeHtml(anchor.selector_value || "")}</span><strong>${escapeHtml(anchor.excerpt ? `${anchor.excerpt.slice(0, 120)}${anchor.excerpt.length > 120 ? "…" : ""}` : "hash-bound")}</strong></div>`).join("") || `<div class="inspector-row"><span>No bounded evidence anchors are recorded.</span></div>`}</div>
      </section>
      <section class="inspector-section">
        <div class="inspector-section-title">Context pack impact</div>
        <div class="inspector-section-body">
          <div class="inspector-row"><span>Selected records</span><strong>${state.context.size}</strong></div>
          <div class="inspector-row"><span>Payload</span><strong>Paths + metadata only</strong></div>
          <div class="safety-note">Context-pack downloads remain metadata-only even when this local explorer includes rendered Markdown bodies.</div>
        </div>
      </section>
      <div class="inspector-actions">
        <button type="button" class="primary-button teal" id="context-toggle">${icon(inContext ? "check" : "plus", "small")}${inContext ? "Added to context pack" : "Add to context pack"}</button>
        ${node.path ? `<a class="secondary-button" href="${escapeHtml(hrefForPath(node.path))}">Open evidence ${icon("fit", "small")}</a>` : ""}
      </div>`;
    inspectorScroll.querySelectorAll("[data-related-id]").forEach((button) => button.addEventListener("click", () => selectNode(button.dataset.relatedId)));
    const contextToggle = $("#context-toggle");
    if (contextToggle) contextToggle.addEventListener("click", () => toggleContext(node.id));
  };

  const pdfEvidence = (node) => {
    const item = (data.document_intelligence?.items || []).find((value) => value.source_id === node.sourceId || value.source_path === node.path || value.source_path === node.authoritativePath);
    if (!item) return "";
    const tree = (item.nodes || []).map((value) => `<li>${escapeHtml(value.title)} <strong>pages ${escapeHtml(String(value.start_page))}–${escapeHtml(String(value.end_page))}</strong></li>`).join("");
    const pages = (item.pages || []).map((page) => `<details><summary>Physical page ${escapeHtml(String(page.page))}${page.truncated ? " · excerpt truncated" : ""}</summary><pre class="doc-path">${escapeHtml(page.excerpt)}</pre><p class="doc-path">Extracted text SHA-256: ${escapeHtml(page.text_hash)}</p></details>`).join("");
    const answers = (item.answers || []).map((answer) => {
      const target = (page) => `${answer.answer_id}-page-${page}`;
      const parts = (values) => values.map((part) => part.page !== undefined ? `<a href="#${escapeHtml(target(part.page))}" data-frozen-page="${escapeHtml(target(part.page))}">[physical page ${escapeHtml(String(part.page))}]</a>` : escapeHtml(part.text)).join("");
      const evidence = (answer.evidence || []).map((value) => `<details id="${escapeHtml(target(value.page))}"><summary>Cited physical page ${escapeHtml(String(value.page))} · frozen evidence</summary><pre class="doc-path">${escapeHtml(value.excerpt)}</pre><p class="doc-path">Source at capture: ${escapeHtml(value.source_path)} · text SHA-256 ${escapeHtml(value.text_hash)}</p></details>`).join("");
      const presentation = answer.presentation;
      const body = presentation?.state === "structured" ? `<h3>Answer</h3><p class="answer-text">${parts(presentation.sections.answer)}</p><h3>Reason</h3><p class="answer-text">${parts(presentation.sections.reason)}</p><h3>Important</h3><p class="answer-text">${parts(presentation.sections.important)}</p><details><summary>Additional detail</summary><p class="answer-text">${parts(presentation.sections.details)}</p></details><details><summary>Complete original generated answer</summary><pre class="doc-path">${escapeHtml(answer.original_answer)}</pre></details>` : `<p>${escapeHtml(presentation?.warning || "Structured presentation unavailable. Review the complete original and its caveats.")}</p><pre class="doc-path">${escapeHtml(answer.original_answer || answer.answer)}</pre>`;
      const freshness = answer.freshness_state === "stale" ? "Historical answer: the source or indexed evidence has changed or is unavailable. This does not establish that the earlier answer was wrong." : answer.freshness_state === "current" ? "Current source and index match. Claim support is unreviewed; citations do not prove correctness." : "Answer unavailable; no conclusion can be inspected.";
      return `<article class="answer-review" aria-label="Unreviewed answer candidate"><h3>Unreviewed answer candidate · ${escapeHtml(answer.freshness_state)}</h3><p>${freshness}</p>${answer.body_content_included ? `<p><strong>Question:</strong> ${escapeHtml(answer.question)}</p>${body}${evidence}` : `<p>${escapeHtml(answer.reason || answer.omission || "Question, answer and excerpts are omitted from metadata-only output.")}</p>`}${answer.context_path ? `<details><summary>Provenance</summary><p><a href="${escapeHtml(hrefForPath(answer.context_path))}">Open frozen evidence pack (JSON)</a></p><p class="doc-path">Source SHA-256: ${escapeHtml(answer.source_hash)} · Model: ${escapeHtml(answer.model)}</p></details>` : ""}</article>`;
    }).join("");
    const emptyPages = item.freshness_state !== "current" ? "Page excerpts are unavailable until the source is synced and reindexed." : "Source text is not embedded here. Generate a local Catalog with --include-content to inspect page excerpts.";
    return `<section aria-label="PDF page evidence"><h2>PDF page evidence · PageIndex</h2><p><strong>${escapeHtml(item.freshness_state)}</strong> · ${escapeHtml(item.method || item.reason || "Index not ready")}</p><p>These are derived navigation and physical PDF page references. They do not certify that a claim is correct.</p>${answers ? `<h3>Answer review</h3><p>Model-generated candidates are not approved conclusions. This Catalog is a saved snapshot; regenerate it to check freshness.</p>${answers}` : "<p>No answer candidate is available. Indexing alone does not generate an answer.</p>"}${item.answer_history_bounded ? "<p>Only a bounded selection of five candidates is shown; more history may exist.</p>" : ""}${item.answer_history_unavailable ? "<p>Answer history could not be safely read.</p>" : ""}<details><summary>Document navigation and page previews</summary>${item.source_hash ? `<p class="doc-path">Source SHA-256: ${escapeHtml(item.source_hash)}</p>` : ""}${tree ? `<ol>${tree}</ol>` : ""}${pages || `<p>${emptyPages}</p>`}${item.omitted_pages ? `<p>${escapeHtml(String(item.omitted_pages))} pages omitted from this bounded preview.</p>` : ""}</details><details><summary>Local next action</summary><p>This passive page does not run commands or call a model.</p><pre class="doc-path">${escapeHtml(item.next_command || "")}</pre></details></section>`;
  };

  const renderMetadata = () => {
    const node = nodeById.get(state.selectedId) || packNode;
    const related = relatedFor(node.id);
    const healthy = isHealthy(node);
    const authority = ["mirror", "repo-note", "machine", "code"].includes(node.kind)
      ? "This record is a derived projection. Its original source remains authoritative and must be used for source-of-truth decisions."
      : node.kind === "curated"
        ? "This note is human-governed knowledge. It should remain traceable to source-backed evidence and review state."
        : "This record represents original or profile-owned evidence. MirrorArc does not modify the authoritative source."
    metadataView.innerHTML = `<article class="document-sheet">
      <p class="doc-eyebrow">Document metadata · ${escapeHtml(kindLabel[node.kind] || "Evidence")}</p>
      <h1>${escapeHtml(node.title)}</h1>
      <div class="doc-meta"><span class="status-pill${healthy ? "" : " attention"}">${icon(healthy ? "check" : "warning", "small")}${escapeHtml(normalizeState(node.state))}</span><span class="status-pill">${escapeHtml(node.domain || "unclassified")}</span><span class="status-pill">${escapeHtml(node.format || node.noteType || "metadata")}</span></div>
      ${pdfEvidence(node)}
      <div class="doc-callout">This view explains provenance, authority, lifecycle, and graph relationships. Use Document view for the rendered Markdown body when this local explorer was generated with content enabled.</div>
      <div class="doc-actions"><button type="button" class="secondary-button" data-open-view="content">${icon("book", "small")}Document view</button><button type="button" class="secondary-button" data-open-view="map">${icon("graph", "small")}Relationship map</button></div>
      <h2>Why this record exists</h2>
      <p>${escapeHtml(node.purpose || `${kindLabel[node.kind] || "This evidence record"} helps reviewers orient to the governed workspace and trace its lifecycle without replacing the original source.`)}</p>
      <h2>Authority boundary</h2>
      <p>${escapeHtml(authority)}</p>
      <div class="metadata-grid">
        <div class="metadata-card"><span>Catalog path</span><strong class="doc-path">${escapeHtml(node.path || "No file path")}</strong></div>
        <div class="metadata-card"><span>Authoritative record</span><strong class="doc-path">${escapeHtml(node.authoritativePath || "Profile metadata")}</strong></div>
        <div class="metadata-card"><span>Stable identity</span><strong>${escapeHtml(node.sourceId || "Not recorded")}</strong></div>
        <div class="metadata-card"><span>Lifecycle contract</span><strong class="doc-path">${escapeHtml(node.lifecycleContract || "Profile / catalog contract")}</strong></div>
      </div>
      <h2>Relationships</h2>
      ${related.length ? `<ul>${related.map(({edge, node: other}) => `<li><strong>${escapeHtml(edge.relation)}</strong> · ${escapeHtml(other.title)} <span class="doc-path">${escapeHtml(other.path || other.domain || "")}</span></li>`).join("")}</ul>` : "<p>No direct relationship is recorded for this item in the portable catalog.</p>"}
      <h2>Prompt-safety boundary</h2>
      <ul>${(data.prompt_safety || []).slice(0, 4).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </article>`;
    metadataView.querySelectorAll("[data-frozen-page]").forEach((link) => link.addEventListener("click", (event) => {
      event.preventDefault();
      const evidence = document.getElementById(link.dataset.frozenPage);
      if (evidence) {
        // Disclosure only: all evidence and freshness came from the backend snapshot.
        for (let parent = evidence; parent && parent !== metadataView; parent = parent.parentElement) {
          if (parent.tagName === "DETAILS") parent.open = true;
        }
        evidence.querySelector("summary").focus();
        evidence.scrollIntoView({block: "nearest"});
      }
    }));
    metadataView.querySelectorAll("[data-open-view]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.openView)));
  };

  const normalizeWikiTarget = (value) => String(value || "").trim().replace(/\\/g, "/").replace(/\.md$/i, "").toLowerCase();
  const resolveWikiTarget = (value) => {
    const target = String(value || "").trim().replace(/\\/g, "/");
    const direct = pathToNode.get(target) || pathToNode.get(`${target}.md`);
    if (direct) return direct;
    const normalized = normalizeWikiTarget(target);
    const match = nodes.find((node) => {
      const path = String(node.path || "");
      const stem = path.split("/").pop()?.replace(/\.md$/i, "") || "";
      return normalizeWikiTarget(node.title) === normalized || normalizeWikiTarget(stem) === normalized || normalizeWikiTarget(path) === normalized;
    });
    return match?.id || "";
  };

  const renderContent = () => {
    const node = nodeById.get(state.selectedId) || packNode;
    const content = contentForPath(node.path);
    const relatedWithContent = relatedFor(node.id).map((item) => item.node).find((item) => contentForPath(item.path));
    let body = "";
    if (content) {
      const markdownLines = stripFrontmatter(content.text).split("\n");
      const titleIndex = markdownLines.findIndex((line) => line.trim());
      if (titleIndex >= 0) {
        const heading = markdownLines[titleIndex].match(/^#\s+(.+)$/);
        if (heading && heading[1].trim().toLowerCase() === String(node.title || "").trim().toLowerCase()) markdownLines.splice(titleIndex, 1);
      }
      body = `<div class="markdown-body">${renderMarkdown(markdownLines.join("\n"))}</div>${content.truncated ? `<div class="doc-callout">This long Markdown body was truncated in the portable explorer. Open the file for the complete record.</div>` : ""}`;
    } else if (relatedWithContent) {
      body = `<div class="content-unavailable">${icon("book", "large")}<h2>Open the generated Markdown mirror</h2><p>This original record is not Markdown, so its readable content lives in the connected mirror.</p><button type="button" class="primary-button teal" data-open-related="${escapeHtml(relatedWithContent.id)}">Read ${escapeHtml(relatedWithContent.title)}</button></div>`;
    } else {
      const explanation = data.document_content_included
        ? "This graph entity does not have a readable Markdown body. Select an authoritative record, L1 projection, or L2 view instead."
        : "This is the safe metadata-only catalog. Regenerate locally with mirrorarc catalog --html --include-content to enable rendered Markdown bodies.";
      body = `<div class="content-unavailable">${icon("book", "large")}<h2>Document body not included</h2><p>${escapeHtml(explanation)}</p></div>`;
    }
    documentView.innerHTML = `<article class="document-sheet">
      <p class="doc-eyebrow">Document view · ${escapeHtml(node.path || kindLabel[node.kind] || "Evidence")}</p>
      <h1>${escapeHtml(node.title)}</h1>
      <div class="doc-meta"><span class="status-pill">${escapeHtml(node.domain || "unclassified")}</span><span class="status-pill">${escapeHtml(node.format || node.noteType || "markdown")}</span></div>
      <div class="doc-actions"><button type="button" class="primary-button teal" data-open-view="map">${icon("graph", "small")}Explore relationships</button><button type="button" class="secondary-button" data-open-view="metadata">Document metadata</button>${node.path ? `<a class="secondary-button" href="${escapeHtml(hrefForPath(node.path))}">Open file ${icon("fit", "small")}</a>` : ""}</div>
      ${body}
    </article>`;
    documentView.querySelectorAll("[data-open-view]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.openView)));
    documentView.querySelectorAll("[data-open-related]").forEach((button) => button.addEventListener("click", () => selectNode(button.dataset.openRelated)));
    documentView.querySelectorAll("[data-wiki-target]").forEach((button) => {
      const id = resolveWikiTarget(button.dataset.wikiTarget);
      if (!id) {
        button.disabled = true;
        button.title = "This linked note is not present in the current catalog.";
      } else {
        button.addEventListener("click", () => selectNode(id));
      }
    });
  };

  const codeRecordForNode = (node) => {
    if (!node) return null;
    if (node.codeRecord) return node.codeRecord;
    const repoId = node.artifactMetadata?.repo_id || (node.kind === "repo" || node.kind === "repo-note" ? node.sourceId : "");
    return repoId ? (codeByRepo.get(repoId) || null) : null;
  };

  const codeEligible = (node) => Boolean(codeRecordForNode(node));
  const rangesLabel = (ranges) => (Array.isArray(ranges) ? ranges : []).map((item) => `L${item.start}–${item.end}`).join(", ") || "Lines not recorded";
  const copyText = async (value) => {
    try {
      await navigator.clipboard.writeText(value);
      showToast("Command copied.");
    } catch (_error) {
      const field = document.createElement("textarea");
      field.value = value;
      field.setAttribute("readonly", "");
      field.style.position = "fixed";
      field.style.opacity = "0";
      document.body.appendChild(field);
      field.select();
      document.execCommand("copy");
      field.remove();
      showToast("Command copied.");
    }
  };

  const renderCode = () => {
    const node = nodeById.get(state.selectedId) || packNode;
    const record = codeRecordForNode(node);
    if (!record) {
      codeView.innerHTML = `<article class="document-sheet"><div class="content-unavailable">${icon("graph", "large")}<h2>Code evidence is available for repositories</h2><p>Select a governed repository or repository mirror to inspect revision-bound analysis.</p></div></article>`;
      return;
    }
    const analysis = record.analysis;
    const stateLabel = String(record.freshness_state || "no-analysis");
    const command = String(record.next_action || `mirrorarc --root . code analyze --repo ${record.repo_id}`);
    if (!analysis) {
      const heading = stateLabel === "failed" ? "Analysis needs attention" : "No analysis yet";
      codeView.innerHTML = `<article class="document-sheet code-dashboard">
        <section class="code-hero"><p class="doc-eyebrow">Code · ${escapeHtml(record.configured_repo || node.title)}</p><h2>${escapeHtml(heading)}</h2><p>${escapeHtml(record.reason || "Run one local analysis command to add revision-bound code evidence.")}</p><div class="code-command"><code>${escapeHtml(command)}</code><button type="button" class="secondary-button" data-copy-code-command>Copy</button></div></section>
        <section class="code-section"><h2>What you will get</h2><p>A repository overview, exact source lines and hashes, an ordered call path, candidate impact, affected-test candidates, and visible limitations. Analysis runs before Catalog generation; this browser never starts a process or fetches data.</p></section>
      </article>`;
      codeView.querySelector("[data-copy-code-command]")?.addEventListener("click", () => copyText(command));
      return;
    }
    const overview = analysis.overview || {};
    const symbols = Array.isArray(analysis.symbols) ? analysis.symbols : [];
    const selectedSymbol = symbols[0] || null;
    const evidence = Array.isArray(analysis.files) ? analysis.files : [];
    const callPath = Array.isArray(analysis.call_path) ? analysis.call_path : [];
    const direct = Array.isArray(analysis.impact?.direct) ? analysis.impact.direct : [];
    const transitive = Array.isArray(analysis.impact?.transitive) ? analysis.impact.transitive : [];
    const tests = Array.isArray(analysis.affected_tests) ? analysis.affected_tests : [];
    const warnings = Array.isArray(analysis.warnings) ? analysis.warnings : [];
    const omissions = Array.isArray(analysis.omissions) ? analysis.omissions : [];
    const languages = Object.entries(overview.languages || {}).map(([name, count]) => `${name} ${count}`).join(" · ") || "Not reported";
    const evidenceRows = evidence.length ? evidence.map((item) => `<tr><td class="doc-path">${escapeHtml(item.path)}</td><td>${escapeHtml(rangesLabel(item.line_ranges))}</td><td class="doc-path">sha256:${escapeHtml(String(item.hash || "").slice(0, 12))}…</td><td>${item.truncated ? "Truncated" : "Complete selected span"} · ${item.excerpt_included ? "Included in this HTML" : "Reference only; body excluded"}${item.excerpt_included && item.excerpt ? `<pre class="code-excerpt">${escapeHtml(item.excerpt)}</pre>` : ""}</td></tr>`).join("") : `<tr><td colspan="4">No exact source span was selected for this overview.</td></tr>`;
    const impactRows = [...direct.map((item) => ({...item, group: "Direct"})), ...transitive.map((item) => ({...item, group: "Transitive"}))];
    const contextCommand = String(record.context_command || `mirrorarc --root . code analyze --repo ${record.repo_id} --context frozen`);
    const current = ["current", "local-uncommitted"].includes(stateLabel);
    codeView.innerHTML = `<article class="document-sheet code-dashboard">
      <section class="code-hero"><p class="doc-eyebrow">Code · ${escapeHtml(record.configured_repo || node.title)}</p><div class="doc-meta"><span class="status-pill${current ? "" : " attention"}">${escapeHtml(normalizeState(stateLabel))}</span><span class="status-pill">${escapeHtml(analysis.analysis_kind || "overview")}</span></div><h2>${escapeHtml(selectedSymbol ? `${selectedSymbol.qualified_name || selectedSymbol.name}` : "Repository overview")}</h2><p>${escapeHtml(record.reason || (selectedSymbol ? `Resolved ${selectedSymbol.kind || "symbol"} to exact source evidence.` : "Current repository structure and entry points."))}</p></section>
      <section class="code-kpis"><div class="code-kpi"><span>Revision</span><strong class="doc-path">${escapeHtml(analysis.resolved_revision || "Not recorded")}</strong></div><div class="code-kpi"><span>Files</span><strong>${escapeHtml(String(overview.file_count || 0))}</strong></div><div class="code-kpi"><span>Languages</span><strong>${escapeHtml(languages)}</strong></div></section>
      <section class="code-section"><h2>Repository overview</h2><p>Key entry points are a bounded backend ranking for orientation, not an authority claim.</p><div class="code-table-wrap"><table class="code-table"><thead><tr><th>Path</th><th>Language</th><th>Symbols</th></tr></thead><tbody>${(overview.key_entry_points || []).map((item) => `<tr><td class="doc-path">${escapeHtml(item.path)}</td><td>${escapeHtml(item.language || "unknown")}</td><td>${escapeHtml(String(item.symbol_count || 0))}</td></tr>`).join("") || `<tr><td colspan="3">No entry points were reported.</td></tr>`}</tbody></table></div></section>
      <section class="code-section"><h2>Exact file and line evidence</h2><p>Selected by the recorded symbol/change request. Other repository files are not included. Mode: ${codeData.content_included ? "local content review" : "metadata only"}; sensitivity: local-sensitive. The frozen export applies its own final byte and file ceilings.</p><div class="code-table-wrap"><table class="code-table"><thead><tr><th>File</th><th>Lines</th><th>File hash</th><th>Coverage</th></tr></thead><tbody>${evidenceRows}</tbody></table></div></section>
      <section class="code-section"><h2>Ordered call path</h2>${callPath.length ? `<ol class="code-path-list">${callPath.map((item) => `<li><div><strong>${escapeHtml(item.name || "Unnamed symbol")}</strong><br><span class="doc-path">${escapeHtml(item.path || "Unknown path")}:${escapeHtml(String(item.start_line || "?"))}</span></div></li>`).join("")}</ol>` : `<p>No bounded call path was requested or resolved.</p>`}</section>
      <section class="code-section"><h2>Change impact</h2><div class="code-table-wrap"><table class="code-table"><thead><tr><th>Scope</th><th>Symbol</th><th>Evidence</th></tr></thead><tbody>${impactRows.map((item) => `<tr><td>${escapeHtml(item.group)}</td><td>${escapeHtml(item.name || item.kind || "Affected item")}</td><td class="doc-path">${escapeHtml(item.path || "Unknown")}:${escapeHtml(String(item.start_line || "?"))}</td></tr>`).join("") || `<tr><td colspan="3">No direct or transitive impact was reported.</td></tr>`}</tbody></table></div><h2>Candidate affected tests</h2>${tests.length ? `<ul>${tests.map((item) => `<li><strong class="doc-path">${escapeHtml(item.path)}</strong> · ${escapeHtml(item.confidence)} confidence · ${escapeHtml(item.basis)}</li>`).join("")}</ul>` : `<p>No candidate affected tests were resolved. This never narrows the repository's normal test gate.</p>`}</section>
      <section class="code-section"><h2>Warnings and omissions</h2><div class="code-warning-list">${warnings.map((item) => `<div class="code-warning">${escapeHtml(item)}</div>`).join("") || `<p>No analysis warning was recorded.</p>`}</div>${omissions.length ? `<details><summary>${omissions.length} omission${omissions.length === 1 ? "" : "s"}</summary><ul>${omissions.map((item) => `<li>${escapeHtml(typeof item === "string" ? item : JSON.stringify(item))}</li>`).join("")}</ul></details>` : ""}</section>
      <section class="code-section"><h2>Add code evidence to context</h2><p>The button adds this bounded analysis to the Catalog's metadata-only selection. Use the command to create a governed frozen pack; passive HTML cannot create one.</p><div class="doc-actions"><button type="button" class="primary-button teal" data-add-code-context>Add code evidence to context</button></div><div class="code-command"><code>${escapeHtml(contextCommand)}</code><button type="button" class="secondary-button" data-copy-context-command>Copy</button></div></section>
    </article>`;
    codeView.querySelector("[data-copy-context-command]")?.addEventListener("click", () => copyText(contextCommand));
    codeView.querySelector("[data-add-code-context]")?.addEventListener("click", () => {
      const analysisNode = nodes.find((item) => item.sourceId === analysis.analysis_id);
      state.context.add(analysisNode?.id || node.id);
      showToast("Code evidence added to the metadata-only selection.");
      renderInspector();
      renderStatus();
    });
  };

  const renderStatus = () => {
    const graph = visibleGraph();
    const selected = nodeById.get(state.selectedId);
    $("#scope-label").textContent = `${state.hops} hop${state.hops === 1 ? "" : "s"} from ${selected ? selected.title : "selection"}`;
    $("#pack-count").textContent = String(state.context.size);
    $("#saved-count").textContent = state.context.size ? `Saved ${state.context.size}` : "Saved";
    $("#graph-node-total").textContent = String(graph.nodes.length);
  };

  const render = () => {
    const selected = nodeById.get(state.selectedId) || packNode;
    const canShowCode = codeEligible(selected);
    $("#code-view-tab").hidden = !canShowCode;
    if (!canShowCode && state.view === "code") state.view = "content";
    renderSidebar();
    renderInspector();
    if (state.view === "map") renderGraph();
    if (state.view === "metadata") renderMetadata();
    if (state.view === "content") renderContent();
    if (state.view === "code") renderCode();
    $$('[data-view]').forEach((button) => button.setAttribute("aria-selected", String(button.dataset.view === state.view)));
    mapView.hidden = state.view !== "map";
    metadataView.hidden = state.view !== "metadata";
    documentView.hidden = state.view !== "content";
    codeView.hidden = state.view !== "code";
    renderStatus();
  };

  const selectNode = (id) => {
    if (!nodeById.has(id)) return;
    state.selectedId = id;
    render();
    closeMobilePanels();
  };

  const toggleContext = (id) => {
    if (!nodeById.has(id) || id === "pack:review") return;
    if (state.context.has(id)) {
      state.context.delete(id);
      showToast("Removed from the local context pack.");
    } else {
      state.context.add(id);
      showToast("Added to the local context pack.");
    }
    render();
  };

  const setView = (view) => {
    const selected = nodeById.get(state.selectedId) || packNode;
    if (view === "code" && !codeEligible(selected)) return;
    state.view = view;
    $$("[data-view]").forEach((button) => button.setAttribute("aria-selected", String(button.dataset.view === view)));
    mapView.hidden = view !== "map";
    metadataView.hidden = view !== "metadata";
    documentView.hidden = view !== "content";
    codeView.hidden = view !== "code";
    $("#fit-button").hidden = view !== "map";
    if (view === "map") {
      renderGraph();
      requestAnimationFrame(fitGraph);
    } else if (view === "metadata") renderMetadata();
    else if (view === "code") renderCode();
    else renderContent();
  };

  const applyScale = () => {
    graphStage.style.transform = `scale(${state.scale})`;
    graphStageSpace.style.width = `${state.graphWidth * state.scale}px`;
    graphStageSpace.style.height = `${state.graphHeight * state.scale}px`;
  };
  const fitGraph = () => {
    if (!graphViewport || graphViewport.clientWidth === 0) return;
    state.scale = Math.max(0.52, Math.min(1, (graphViewport.clientWidth - 24) / state.graphWidth, (graphViewport.clientHeight - 20) / state.graphHeight));
    state.manualScale = false;
    applyScale();
    graphViewport.scrollTo({left: 0, top: 0, behavior: "smooth"});
  };
  const zoom = (delta) => {
    state.scale = Math.max(0.45, Math.min(1.35, state.scale + delta));
    state.manualScale = true;
    applyScale();
  };

  const catalogWidthLimits = () => ({min: 220, max: Math.max(220, Math.min(480, window.innerWidth - 580))});
  const setCatalogWidth = (value, {persist = true} = {}) => {
    if (window.innerWidth <= 820) return;
    const limits = catalogWidthLimits();
    state.catalogWidth = Math.round(Math.max(limits.min, Math.min(limits.max, Number(value) || 280)));
    document.documentElement.style.setProperty("--catalog-width", `${state.catalogWidth}px`);
    if (leftResizer) {
      leftResizer.setAttribute("aria-valuemin", String(limits.min));
      leftResizer.setAttribute("aria-valuemax", String(limits.max));
      leftResizer.setAttribute("aria-valuenow", String(state.catalogWidth));
    }
    if (persist) {
      try { window.localStorage.setItem("mirrorarc-catalog-width", String(state.catalogWidth)); } catch (_error) { /* portable file mode may disable storage */ }
    }
    if (!state.manualScale && state.view === "map") requestAnimationFrame(fitGraph);
  };
  try {
    const savedCatalogWidth = Number(window.localStorage.getItem("mirrorarc-catalog-width"));
    if (savedCatalogWidth) state.catalogWidth = savedCatalogWidth;
  } catch (_error) { /* use the default width */ }
  setCatalogWidth(state.catalogWidth, {persist: false});

  if (leftResizer) {
    let resizeStartX = 0;
    let resizeStartWidth = state.catalogWidth;
    const stopResize = () => {
      leftResizer.classList.remove("resizing");
      document.body.style.userSelect = "";
    };
    leftResizer.addEventListener("pointerdown", (event) => {
      if (window.innerWidth <= 820) return;
      resizeStartX = event.clientX;
      resizeStartWidth = state.catalogWidth;
      leftResizer.setPointerCapture(event.pointerId);
      leftResizer.classList.add("resizing");
      document.body.style.userSelect = "none";
    });
    leftResizer.addEventListener("pointermove", (event) => {
      if (!leftResizer.hasPointerCapture(event.pointerId)) return;
      setCatalogWidth(resizeStartWidth + event.clientX - resizeStartX);
    });
    leftResizer.addEventListener("pointerup", (event) => {
      if (leftResizer.hasPointerCapture(event.pointerId)) leftResizer.releasePointerCapture(event.pointerId);
      stopResize();
    });
    leftResizer.addEventListener("pointercancel", stopResize);
    leftResizer.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const limits = catalogWidthLimits();
      if (event.key === "Home") setCatalogWidth(limits.min);
      else if (event.key === "End") setCatalogWidth(limits.max);
      else setCatalogWidth(state.catalogWidth + (event.key === "ArrowRight" ? 20 : -20));
    });
  }

  let toastTimer = null;
  const showToast = (message) => {
    const toast = $("#toast");
    $("#toast-message").textContent = message;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 2200);
  };

  const openMobilePanel = (which) => {
    closeMobilePanels();
    (which === "left" ? leftPanel : rightPanel).classList.add("open");
    mobileBackdrop.classList.add("open");
  };
  const closeMobilePanels = () => {
    leftPanel.classList.remove("open");
    rightPanel.classList.remove("open");
    mobileBackdrop.classList.remove("open");
  };

  const contextPayload = () => Array.from(state.context).map((id) => nodeById.get(id)).filter(Boolean).map((node) => ({
    id: node.sourceId || node.id,
    title: node.title,
    kind: kindLabel[node.kind] || node.kind,
    path: node.path || null,
    authoritative_source: node.authoritativePath || null,
    domain: node.domain || null,
    lifecycle_state: node.state || null,
    layer: node.layer || null,
    authority: node.authority || null,
    source_sha256: node.sourceSha256 || null,
    warnings: node.warnings || 0,
    errors: node.errors || 0,
    relationships: relatedFor(node.id).map(({edge, node: other}) => ({
      relation: edge.relation,
      state: edge.relationshipState || "accepted",
      target: other.path || other.title,
      evidence_anchors: (edge.evidence || []).map((anchor) => ({selector_type: anchor.selector_type, selector_value: anchor.selector_value, source_hash: anchor.source_hash}))
    }))
  }));
  const contextMarkdown = () => {
    const items = contextPayload();
    return [
      "# MirrorArc Context Pack",
      "",
      "> Metadata-only export from CATALOG.html. Source and mirror bodies are excluded.",
      "",
      ...items.flatMap((item) => [
        `## ${item.title}`,
        "",
        `- Kind: ${item.kind}`,
        `- Path: ${item.path || "not recorded"}`,
        `- Authoritative source: ${item.authoritative_source || "not recorded"}`,
        `- Domain: ${item.domain || "unclassified"}`,
        `- Lifecycle: ${item.lifecycle_state || "unknown"}`,
        `- Layer / authority: ${item.layer || "unlayered"} / ${item.authority || "not recorded"}`,
        `- Warnings / errors: ${item.warnings} / ${item.errors}`,
        ...(item.relationships.length ? ["- Relationships:", ...item.relationships.map((rel) => `  - ${rel.relation}: ${rel.target}`)] : []),
        ""
      ])
    ].join("\n");
  };
  const download = (filename, content, type) => {
    const blob = new Blob([content], {type});
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  const renderPackModal = () => {
    const items = contextPayload();
    const list = $("#pack-list");
    list.innerHTML = items.length ? items.map((item) => `<div class="pack-item">${icon("fileMd", "small")}<strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.kind)}</span></div>`).join("") : `<div class="sidebar-empty">Select evidence, then add it to the context pack.</div>`;
    const governed = (projectionData.context_definitions || []).map((definition) => `<div class="safety-note"><strong>${escapeHtml(definition.name)}</strong><p>Task: ${escapeHtml(definition.selection?.query || definition.purpose)} · Dynamic definition; resolve to inspect current selection, ranking, spans and exclusions.</p><pre class="code-command">${escapeHtml(definition.resolve_command || "")}</pre><p>Create an allowed frozen export after inspecting the evidence:</p><pre class="code-command">${escapeHtml(definition.freeze_command || "")}</pre></div>`).join("");
    const packs = (projectionData.context_packs || []).map((pack) => `<div class="safety-note"><strong>Frozen evidence · ${escapeHtml(pack.freshness_state)}</strong><p>${escapeHtml(String(pack.included_count))} included / ${escapeHtml(String(pack.selection_count))} selected · ${escapeHtml(pack.sensitivity)} · ${escapeHtml(String((pack.omissions || []).length))} omissions</p><span class="doc-path">${escapeHtml(pack.output_path)}</span></div>`).join("");
    $("#governed-contexts").innerHTML = `<h3>Governed task context</h3>${governed || "<p>No saved task yet. Choose a query in the CLI, inspect its evidence, then export an allowed frozen pack.</p>"}${packs}`;
    $("#pack-summary").textContent = `${items.length} selected record${items.length === 1 ? "" : "s"}. Paths, lifecycle metadata, provenance, and relationships only.`;
    $("#download-md").disabled = !items.length;
    $("#download-json").disabled = !items.length;
  };
  const openPackModal = () => {
    renderPackModal();
    $("#pack-modal-backdrop").classList.add("open");
    $("#pack-modal-close").focus();
  };
  const closePackModal = () => {
    const wasOpen = $("#pack-modal-backdrop").classList.contains("open");
    $("#pack-modal-backdrop").classList.remove("open");
    if (wasOpen) $("#build-context").focus();
  };

  $$("[data-view]").forEach((button) => button.addEventListener("click", () => setView(button.dataset.view)));
  $$("[data-hop]").forEach((button) => button.addEventListener("click", () => {
    state.hops = Number(button.dataset.hop);
    $$("[data-hop]").forEach((item) => item.setAttribute("aria-pressed", String(Number(item.dataset.hop) === state.hops)));
    renderGraph();
    renderStatus();
  }));
  $$("[data-sidebar-tab]").forEach((button) => button.addEventListener("click", () => {
    state.sidebarTab = button.dataset.sidebarTab;
    $$("[data-sidebar-tab]").forEach((item) => item.setAttribute("aria-selected", String(item.dataset.sidebarTab === state.sidebarTab)));
    renderSidebar();
  }));
  $("#filter-button").addEventListener("click", () => {
    $("#filter-popover").classList.toggle("open");
    $("#filter-button").classList.toggle("active", $("#filter-popover").classList.contains("open"));
  });
  $$("[data-filter]").forEach((input) => input.addEventListener("change", () => {
    input.checked ? state.filters.add(input.dataset.filter) : state.filters.delete(input.dataset.filter);
    renderSidebar();
  }));
  const relationshipFilter = $("#relationship-filter");
  if (relationshipFilter) {
    Array.from(new Set(baseEdges.map((edge) => edge.relation))).sort().forEach((relation) => {
      const option = document.createElement("option");
      option.value = relation;
      option.textContent = relation;
      relationshipFilter.appendChild(option);
    });
    relationshipFilter.addEventListener("change", () => {
      state.relationshipFilter = relationshipFilter.value;
      renderSidebar();
    });
  }
  const syncSearch = (value) => {
    state.search = value;
    $("#global-search-input").value = value;
    $("#sidebar-search-input").value = value;
    renderSidebar();
  };
  $("#global-search-input").addEventListener("input", (event) => syncSearch(event.target.value));
  $("#sidebar-search-input").addEventListener("input", (event) => syncSearch(event.target.value));
  document.addEventListener("keydown", (event) => {
    if (event.key === "Tab" && $("#pack-modal-backdrop").classList.contains("open")) {
      const controls = Array.from($("#pack-modal-backdrop").querySelectorAll("button:not(:disabled), a[href], input, [tabindex='0']"));
      const first = controls[0], last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      $("#global-search-input").focus();
    }
    if (event.key === "Escape") {
      closeMobilePanels();
      closePackModal();
    }
  });
  $("#fit-button").addEventListener("click", fitGraph);
  $("#zoom-in").addEventListener("click", () => zoom(0.1));
  $("#zoom-out").addEventListener("click", () => zoom(-0.1));
  $("#zoom-fit").addEventListener("click", fitGraph);
  $("#open-left").addEventListener("click", () => openMobilePanel("left"));
  $("#open-right").addEventListener("click", () => openMobilePanel("right"));
  $("#inspector-close").addEventListener("click", closeMobilePanels);
  mobileBackdrop.addEventListener("click", closeMobilePanels);
  $("#build-context").addEventListener("click", openPackModal);
  $("#pack-modal-close").addEventListener("click", closePackModal);
  $("#pack-modal-cancel").addEventListener("click", closePackModal);
  $("#pack-modal-backdrop").addEventListener("click", (event) => {
    if (event.target.id === "pack-modal-backdrop") closePackModal();
  });
  $("#download-md").addEventListener("click", () => download("mirrorarc-context-pack.md", contextMarkdown(), "text/markdown;charset=utf-8"));
  $("#download-json").addEventListener("click", () => download("mirrorarc-context-pack.json", JSON.stringify({generated_by: "MirrorArc CATALOG.html", metadata_only: true, items: contextPayload()}, null, 2), "application/json;charset=utf-8"));
  $("#add-collection").addEventListener("click", () => showToast("Collections come from the active MirrorArc profile contract."));
  $("#help-button").addEventListener("click", () => showToast("Select an item to trace provenance, inspect lifecycle metadata, or add it to a local context pack."));
  window.addEventListener("resize", () => {
    setCatalogWidth(state.catalogWidth, {persist: false});
    if (!state.manualScale && state.view === "map") fitGraph();
  });

  render();
  setView("content");
})();
"""


def render_catalog_explorer(
    report: dict[str, Any],
    warnings: list[str],
    errors: list[str],
    *,
    max_items: int = 500,
) -> str:
    source_items, hidden_sources = _limited(report.get("source_items", []), max_items)
    unmanaged_sources, hidden_unmanaged = _limited(report.get("unmanaged_sources", []), max_items)
    repo_items, hidden_repos = _limited(report.get("repo_items", []), max_items)
    curated_items, hidden_curated = _limited(report.get("curated_items", []), max_items)
    machine_owned_items, hidden_machine = _limited(report.get("machine_owned_items", []), max_items)
    payload = {
        "profile": report.get("profile", {}),
        "summary": report.get("summary", {}),
        "domains": report.get("domains", []),
        "states": report.get("states", {}),
        "repo_states": report.get("repo_states", {}),
        "formats": report.get("formats", {}),
        "source_items": source_items,
        "repo_items": repo_items,
        "curated_items": curated_items,
        "machine_owned_items": machine_owned_items,
        "unmanaged_sources": unmanaged_sources,
        "warnings": warnings,
        "errors": errors,
        "prompt_safety": report.get("prompt_safety", []),
        "knowledge_projection": report.get("knowledge_projection", {}),
        "code_intelligence": report.get("code_intelligence", {}),
        "document_intelligence": report.get("document_intelligence", {}),
        "document_content": report.get("document_content", {}),
        "document_content_included": bool(report.get("document_content_included", False)),
        "hidden_counts": {
            "source": hidden_sources,
            "unmanaged": hidden_unmanaged,
            "repo": hidden_repos,
            "curated": hidden_curated,
            "machine_owned": hidden_machine,
            "total": hidden_sources + hidden_unmanaged + hidden_repos + hidden_curated + hidden_machine,
        },
    }
    profile = payload["profile"] if isinstance(payload["profile"], dict) else {}
    profile_name = str(profile.get("name") or profile.get("id") or "Workspace")
    source_count = int(payload["summary"].get("source_records", 0)) if isinstance(payload["summary"], dict) else 0
    warning_count = len(warnings) + len(errors)
    data_json = _script_json(payload)
    content_mode_label = (
        "Local content-inclusive · contains rendered Markdown"
        if payload["document_content_included"]
        else "Portable metadata-only catalog"
    )

    return "".join(
        [
            "<!doctype html>\n",
            '<html lang="en">\n<head>\n',
            '<meta charset="utf-8">\n',
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n',
            '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; script-src \'unsafe-inline\'; img-src data:; object-src \'none\'; base-uri \'none\'; form-action \'none\'">\n',
            "<title>MirrorArc Catalog Explorer</title>\n",
            "<style>",
            EXPLORER_CSS,
            "</style>\n</head>\n<body>\n",
            '<div class="app-shell">\n',
            '<header class="app-header">',
            '<div class="brand-cluster"><span class="brand">MirrorArc</span>',
            '<div class="profile-chip" title="Active profile"><svg class="icon small" viewBox="0 0 256 256" aria-hidden="true"><path d="M230.91,172A8,8,0,0,1,228,182.91l-96,56a8,8,0,0,1-8.06,0l-96-56A8,8,0,0,1,36,169.09l92,53.65,92-53.65A8,8,0,0,1,230.91,172ZM220,121.09l-92,53.65L36,121.09A8,8,0,0,0,28,134.91l96,56a8,8,0,0,0,8.06,0l96-56A8,8,0,1,0,220,121.09ZM24,80a8,8,0,0,1,4-6.91l96-56a8,8,0,0,1,8.06,0l96,56a8,8,0,0,1,0,13.82l-96,56a8,8,0,0,1-8.06,0l-96-56A8,8,0,0,1,24,80Zm23.88,0L128,126.74,208.12,80,128,33.26Z"></path></svg><span>',
            profile_name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"),
            '</span></div></div>',
            '<label class="global-search"><span class="sr-only">Search catalog</span><svg class="icon" viewBox="0 0 256 256" aria-hidden="true"><path d="M229.66,218.34l-50.07-50.06a88.11,88.11,0,1,0-11.31,11.31l50.06,50.07a8,8,0,0,0,11.32-11.32ZM40,112a72,72,0,1,1,72,72A72.08,72.08,0,0,1,40,112Z"></path></svg><input id="global-search-input" type="search" placeholder="Search documents, notes, relationships…" autocomplete="off"><span class="keycap">⌘K</span></label>',
            '<div class="header-actions"><div class="sync-state" title="Content-inclusive catalogs are for local review and may contain sensitive workspace content."><svg class="icon small" viewBox="0 0 256 256" aria-hidden="true"><path d="M173.66,98.34a8,8,0,0,1,0,11.32l-56,56a8,8,0,0,1-11.32,0l-24-24a8,8,0,0,1,11.32-11.32L112,148.69l50.34-50.35A8,8,0,0,1,173.66,98.34ZM232,128A104,104,0,1,1,128,24,104.11,104.11,0,0,1,232,128Zm-16,0a88,88,0,1,0-88,88A88.1,88.1,0,0,0,216,128Z"></path></svg><span>',
            content_mode_label,
            '</span></div>',
            '<button type="button" class="icon-button help-button" id="help-button" aria-label="Explorer help">?</button>',
            '<button type="button" class="primary-button" id="build-context"><svg class="icon small" viewBox="0 0 256 256" aria-hidden="true"><path d="M230.91,172A8,8,0,0,1,228,182.91l-96,56a8,8,0,0,1-8.06,0l-96-56A8,8,0,0,1,36,169.09l92,53.65,92-53.65A8,8,0,0,1,230.91,172ZM220,121.09l-92,53.65L36,121.09A8,8,0,0,0,28,134.91l96,56a8,8,0,0,0,8.06,0l96-56A8,8,0,1,0,220,121.09ZM24,80a8,8,0,0,1,4-6.91l96-56a8,8,0,0,1,8.06,0l96,56a8,8,0,0,1,0,13.82l-96,56a8,8,0,0,1-8.06,0l-96-56A8,8,0,0,1,24,80Zm23.88,0L128,126.74,208.12,80,128,33.26Z"></path></svg>Build context pack</button></div>',
            "</header>\n",
            '<main class="workspace">',
            '<aside class="left-panel" id="left-panel" aria-label="Catalog browse panel">',
            '<div class="panel-tabs" role="tablist" aria-label="Catalog navigation"><button type="button" class="tab-button" data-sidebar-tab="browse" aria-selected="true">Browse</button><button type="button" class="tab-button" data-sidebar-tab="saved" aria-selected="false"><span id="saved-count">Saved</span></button><button type="button" class="filter-button" id="filter-button"><svg class="icon small" viewBox="0 0 256 256" aria-hidden="true"><path d="M200,136a8,8,0,0,1-8,8H64a8,8,0,0,1,0-16H192A8,8,0,0,1,200,136Zm32-56H24a8,8,0,0,0,0,16H232a8,8,0,0,0,0-16Zm-80,96H104a8,8,0,0,0,0,16h48a8,8,0,0,0,0-16Z"></path></svg>Filters</button></div>',
            '<label class="sidebar-search"><span class="sr-only">Filter this vault</span><svg class="icon small" viewBox="0 0 256 256" aria-hidden="true"><path d="M229.66,218.34l-50.07-50.06a88.11,88.11,0,1,0-11.31,11.31l50.06,50.07a8,8,0,0,0,11.32-11.32ZM40,112a72,72,0,1,1,72,72A72.08,72.08,0,0,1,40,112Z"></path></svg><input id="sidebar-search-input" type="search" placeholder="Filter this vault" autocomplete="off"></label>',
            '<div class="filter-popover" id="filter-popover"><label class="filter-choice"><input type="checkbox" data-filter="healthy">Current</label><label class="filter-choice"><input type="checkbox" data-filter="attention">Attention</label><label class="filter-choice"><input type="checkbox" data-filter="sources">Sources</label><label class="filter-choice"><input type="checkbox" data-filter="notes">Notes/views</label><label class="filter-choice"><input type="checkbox" data-filter="l0">L0 sources</label><label class="filter-choice"><input type="checkbox" data-filter="l1">L1 projections</label><label class="filter-choice"><input type="checkbox" data-filter="l2">L2 views</label><label class="filter-choice"><input type="checkbox" data-filter="stale">Stale</label><label class="filter-choice"><input type="checkbox" data-filter="reviewed">Reviewed</label><label class="filter-choice relationship-filter-label">Relationship<select id="relationship-filter"><option value="">Any type</option></select></label></div>',
            '<div class="pinned-index" id="pinned-index" aria-label="Start here"></div>',
            '<div class="collection-scroll" id="collection-scroll"></div>',
            '<button type="button" class="add-collection" id="add-collection"><svg class="icon small" viewBox="0 0 256 256" aria-hidden="true"><path d="M224,128a8,8,0,0,1-8,8H136v80a8,8,0,0,1-16,0V136H40a8,8,0,0,1,0-16h80V40a8,8,0,0,1,16,0v80h80A8,8,0,0,1,224,128Z"></path></svg>Add collection</button>',
            "</aside>",
            '<div class="panel-resizer" id="left-resizer" role="separator" aria-label="Resize catalog panel" aria-orientation="vertical" aria-valuemin="220" aria-valuemax="480" aria-valuenow="280" tabindex="0" title="Drag or use arrow keys to resize the catalog"></div>',
            '<section class="center-panel" aria-label="Catalog workspace">',
            '<div class="center-toolbar"><button type="button" class="mobile-panel-button" id="open-left">Browse</button><div class="segmented" role="tablist" aria-label="Center view"><button type="button" data-view="map" aria-label="Relationship map" aria-selected="false"><span class="tab-label-long">Relationship map</span><span class="tab-label-short">Map</span></button><button type="button" data-view="metadata" aria-label="Document metadata" aria-selected="false"><span class="tab-label-long">Document metadata</span><span class="tab-label-short">Metadata</span></button><button type="button" data-view="content" aria-label="Document view" aria-selected="true"><span class="tab-label-long">Document view</span><span class="tab-label-short">Document</span></button><button type="button" data-view="code" id="code-view-tab" aria-label="Code evidence" aria-selected="false" hidden>Code</button></div><span class="toolbar-spacer"></span><button type="button" class="fit-button" id="fit-button" hidden><svg class="icon small" viewBox="0 0 256 256" aria-hidden="true"><path d="M216,48V96a8,8,0,0,1-16,0V67.31l-50.34,50.35a8,8,0,0,1-11.32-11.32L188.69,56H160a8,8,0,0,1,0-16h48A8,8,0,0,1,216,48ZM106.34,138.34,56,188.69V160a8,8,0,0,0-16,0v48a8,8,0,0,0,8,8H96a8,8,0,0,0,0-16H67.31l50.35-50.34a8,8,0,0,0-11.32-11.32Z"></path></svg><span>Fit to view</span></button><button type="button" class="mobile-panel-button" id="open-right">Inspect</button></div>',
            '<div class="map-view" id="map-view" hidden><div class="map-controls"><strong>Focus</strong><div class="hop-control" aria-label="Relationship depth"><button type="button" data-hop="1" aria-pressed="false">1 hop</button><button type="button" data-hop="2" aria-pressed="true">2 hops</button><button type="button" data-hop="3" aria-pressed="false">3 hops</button></div><span class="map-hint">Select any entity to inspect its evidence</span></div><div class="graph-viewport" id="graph-viewport"><div class="graph-stage-space" id="graph-stage-space"><div class="graph-stage" id="graph-stage"></div></div><div class="zoom-controls" aria-label="Map zoom"><button type="button" id="zoom-in" aria-label="Zoom in">+</button><button type="button" id="zoom-out" aria-label="Zoom out">−</button><button type="button" id="zoom-fit" aria-label="Fit graph"><svg class="icon small" viewBox="0 0 256 256" aria-hidden="true"><path d="M216,48V96a8,8,0,0,1-16,0V67.31l-50.34,50.35a8,8,0,0,1-11.32-11.32L188.69,56H160a8,8,0,0,1,0-16h48A8,8,0,0,1,216,48ZM106.34,138.34,56,188.69V160a8,8,0,0,0-16,0v48a8,8,0,0,0,8,8H96a8,8,0,0,0,0-16H67.31l50.35-50.34a8,8,0,0,0-11.32-11.32Z"></path></svg></button></div></div><div class="legend"><span class="legend-item source"><svg class="icon" viewBox="0 0 256 256" aria-hidden="true"><path d="M52,144H36a8,8,0,0,0-8,8v56a8,8,0,0,0,8,8H52a36,36,0,0,0,0-72Zm0,56H44V160h8a20,20,0,0,1,0,40Z"></path></svg>Original source</span><span class="legend-item mirror"><svg class="icon" viewBox="0 0 256 256" aria-hidden="true"><path d="M213.66,82.34l-56-56A8,8,0,0,0,152,24H56A16,16,0,0,0,40,40v72a8,8,0,0,0,16,0V40h88V88a8,8,0,0,0,8,8h48V224a8,8,0,0,0,16,0V88A8,8,0,0,0,213.66,82.34Z"></path></svg>L1 projection</span><span class="legend-item"><svg class="icon" viewBox="0 0 256 256" aria-hidden="true"><path d="M213.66,82.34l-56-56A8,8,0,0,0,152,24H56A16,16,0,0,0,40,40v72a8,8,0,0,0,16,0V40h88V88a8,8,0,0,0,8,8h48V224a8,8,0,0,0,16,0V88A8,8,0,0,0,213.66,82.34Z"></path></svg>Governed record / L2 view</span><span class="legend-item review"><svg class="icon" viewBox="0 0 256 256" aria-hidden="true"><path d="M235.32,81.37,174.63,20.69a16,16,0,0,0-22.63,0L98.37,74.49c-10.66-3.34-35-7.37-60.4,13.14a16,16,0,0,0-1.29,23.78L85,159.71,42.34,202.34a8,8,0,0,0,11.32,11.32L96.29,171l48.29,48.29A16,16,0,0,0,155.9,224Z"></path></svg>Lifecycle review</span><span class="legend-item pack"><svg class="icon" viewBox="0 0 256 256" aria-hidden="true"><path d="M230.91,172A8,8,0,0,1,228,182.91l-96,56a8,8,0,0,1-8.06,0l-96-56A8,8,0,0,1,36,169.09l92,53.65,92-53.65A8,8,0,0,1,230.91,172Z"></path></svg>Context pack</span></div></div>',
            '<div class="document-view" id="metadata-view" hidden></div>',
            '<div class="document-view" id="document-view"></div>',
            '<div class="document-view" id="code-view" hidden></div>',
            "</section>",
            '<aside class="right-panel" id="right-panel" aria-label="Evidence inspector"><div class="inspector-header"><h2>Evidence Inspector</h2><span class="spacer"></span><button type="button" class="plain-icon-button" aria-label="Pin inspector"><svg class="icon small" viewBox="0 0 256 256" aria-hidden="true"><path d="M235.32,81.37,174.63,20.69a16,16,0,0,0-22.63,0L98.37,74.49c-10.66-3.34-35-7.37-60.4,13.14a16,16,0,0,0-1.29,23.78L85,159.71,42.34,202.34a8,8,0,0,0,11.32,11.32L96.29,171l48.29,48.29A16,16,0,0,0,155.9,224Z"></path></svg></button><button type="button" class="plain-icon-button" id="inspector-close" aria-label="Close inspector"><svg class="icon small" viewBox="0 0 256 256" aria-hidden="true"><path d="M205.66,194.34a8,8,0,0,1-11.32,11.32L128,139.31,61.66,205.66a8,8,0,0,1-11.32-11.32L116.69,128,50.34,61.66A8,8,0,0,1,61.66,50.34L128,116.69l66.34-66.35a8,8,0,0,1,11.32,11.32L139.31,128Z"></path></svg></button></div><div class="inspector-scroll" id="inspector-scroll"></div></aside>',
            "</main>",
            '<footer class="status-bar"><span>Graph scope: <strong id="scope-label">2 hops</strong></span><span class="separator">|</span><span class="hidden-count">Hidden nodes: <strong id="hidden-node-count">0</strong></span><span class="separator">|</span><span>Visible: <strong id="graph-node-total">0</strong></span><span class="separator">|</span><span>Context pack: <strong id="pack-count">0</strong></span><span class="authority">Derived, rebuildable view · original records remain authoritative</span></footer>',
            "</div>",
            '<div class="mobile-backdrop" id="mobile-backdrop"></div>',
            '<div class="toast" id="toast" role="status" aria-live="polite"><svg class="icon small" viewBox="0 0 256 256" aria-hidden="true"><path d="M173.66,98.34a8,8,0,0,1,0,11.32l-56,56a8,8,0,0,1-11.32,0l-24-24a8,8,0,0,1,11.32-11.32L112,148.69l50.34-50.35A8,8,0,0,1,173.66,98.34Z"></path></svg><span id="toast-message"></span></div>',
            '<div class="modal-backdrop" id="pack-modal-backdrop"><section class="modal" role="dialog" aria-modal="true" aria-labelledby="pack-modal-title"><div class="modal-header"><svg class="icon large" viewBox="0 0 256 256" aria-hidden="true"><path d="M230.91,172A8,8,0,0,1,228,182.91l-96,56a8,8,0,0,1-8.06,0l-96-56A8,8,0,0,1,36,169.09l92,53.65,92-53.65A8,8,0,0,1,230.91,172Z"></path></svg><h2 id="pack-modal-title">Export selection manifest</h2><span class="spacer"></span><button type="button" class="plain-icon-button" id="pack-modal-close" aria-label="Close context pack"><svg class="icon small" viewBox="0 0 256 256" aria-hidden="true"><path d="M205.66,194.34a8,8,0,0,1-11.32,11.32L128,139.31,61.66,205.66a8,8,0,0,1-11.32-11.32L116.69,128,50.34,61.66A8,8,0,0,1,61.66,50.34L128,116.69l66.34-66.35a8,8,0,0,1,11.32,11.32L139.31,128Z"></path></svg></button></div><div class="modal-body"><p id="pack-summary"></p><div class="safety-note">This portable export contains catalog paths and metadata only. It never copies source text, mirror bodies, secrets, or review-note content.</div><div class="pack-list" id="pack-list"></div><section id="governed-contexts"></section></div><div class="modal-actions"><button type="button" class="secondary-button" id="pack-modal-cancel">Cancel</button><button type="button" class="secondary-button" id="download-json"><svg class="icon small" viewBox="0 0 256 256" aria-hidden="true"><path d="M224,144v64a8,8,0,0,1-8,8H40a8,8,0,0,1-8-8V144a8,8,0,0,1,16,0v56H208V144a8,8,0,0,1,16,0Z"></path></svg>JSON</button><button type="button" class="primary-button teal" id="download-md"><svg class="icon small" viewBox="0 0 256 256" aria-hidden="true"><path d="M224,144v64a8,8,0,0,1-8,8H40a8,8,0,0,1-8-8V144a8,8,0,0,1,16,0v56H208V144a8,8,0,0,1,16,0Z"></path></svg>Markdown</button></div></section></div>',
            '<script type="application/json" id="mirrorarc-catalog-data">',
            data_json,
            "</script>\n<script>",
            EXPLORER_JS,
            "</script>\n",
            f'<!-- Generated by mirrorarc catalog --html. Source records: {source_count}; catalog warnings/errors: {warning_count}. -->\n',
            "</body>\n</html>\n",
        ]
    )
