#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Create a private plain-Markdown conversion dump for benchmark baselines."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

try:
    from markitdown import MarkItDown
except ImportError:
    sys.exit("Missing dependency: pip install 'markitdown[docx,pptx,xlsx,pdf]'")

from noeticweave.mirrors import office as office_sync


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = Path("_benchmark/plain_markitdown_dump")
DEFAULT_SUMMARY_PATH = Path("_benchmark/plain_markitdown_dump-summary.json")
DEFAULT_EXTENSIONS = {".docx", ".pptx", ".xlsx"}
PDF_EXTENSIONS = {".pdf"}


def in_source_checkout(path: Path) -> bool:
    resolved = path.expanduser().resolve()
    return resolved == ROOT or ROOT in resolved.parents


def safe_rel_path(value: str, label: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"{label} must be a relative path inside the vault")
    if path == Path(".") or len(path.parts) < 2:
        raise ValueError(f"{label} must name a nested private output path, such as _benchmark/plain_markitdown_dump")
    for part in path.parts:
        if part.startswith("."):
            raise ValueError(f"{label} must not contain hidden path components")
    return path


def reset_output(root: Path, output_root: Path, *, force: bool) -> None:
    target = root / output_root
    if not target.exists():
        return
    if not force:
        raise ValueError(f"{output_root.as_posix()} already exists; use --force to replace it")
    if target.is_file() or target.is_symlink():
        target.unlink()
    else:
        shutil.rmtree(target)


def source_extensions(*, include_pdf: bool) -> set[str]:
    extensions = set(DEFAULT_EXTENSIONS)
    if include_pdf:
        extensions.update(PDF_EXTENSIONS)
    return extensions


def iter_sources(root: Path, output_root: Path, *, include_pdf: bool) -> list[Path]:
    extensions = source_extensions(include_pdf=include_pdf)
    sources: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if rel.parts[: len(output_root.parts)] == output_root.parts:
            continue
        if office_sync.is_excluded(rel, mirror_root=Path(office_sync.DEFAULT_MIRROR_ROOT)):
            continue
        if path.suffix.lower() not in extensions:
            continue
        if office_sync.source_path_error(root, path):
            continue
        sources.append(path)
    return sources


def dump_path(output_root: Path, source_rel: Path) -> Path:
    return output_root / source_rel.with_suffix(".md")


def render_dump(source_rel: Path, source_format: str, text: str) -> str:
    cleaned = office_sync.clean_extracted_text(source_format, text).strip()
    if not cleaned:
        cleaned = "_No text extracted by plain MarkItDown conversion._"
    return "\n".join(
        [
            "# Plain MarkItDown Dump",
            "",
            f"Source: `{source_rel.as_posix()}`",
            "",
            "> Baseline-only conversion. No NoeticWeave manifest identity, lifecycle state,",
            "> generated-mirror sentinel, review ledger, or curated hub context is attached.",
            "",
            cleaned,
            "",
        ]
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def create_dump(
    root: Path,
    *,
    output_root: Path,
    summary_path: Path,
    include_pdf: bool,
    force: bool,
    allow_source_checkout_root: bool,
) -> dict[str, Any]:
    root = root.expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"vault root does not exist or is not a directory: {root}")
    if in_source_checkout(root) and not allow_source_checkout_root:
        raise ValueError("refusing to write private benchmark output inside the NoeticWeave source checkout")
    reset_output(root, output_root, force=force)
    converter = MarkItDown()
    records: list[dict[str, Any]] = []
    converted = 0
    errors = 0
    for source in iter_sources(root, output_root, include_pdf=include_pdf):
        rel = source.relative_to(root)
        out_rel = dump_path(output_root, rel)
        try:
            result = converter.convert(str(source))
            text = getattr(result, "text_content", "")
            write_text(root / out_rel, render_dump(rel, source.suffix.lower(), text))
        except Exception as exc:  # pragma: no cover - exact converter failures vary by backend
            errors += 1
            records.append(
                {
                    "source_path": rel.as_posix(),
                    "dump_path": out_rel.as_posix(),
                    "status": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue
        converted += 1
        records.append(
            {
                "source_path": rel.as_posix(),
                "dump_path": out_rel.as_posix(),
                "status": "converted",
            }
        )
    summary = {
        "schema_version": 1,
        "output_root": output_root.as_posix(),
        "include_pdf": include_pdf,
        "converted": converted,
        "errors": errors,
        "records": records,
    }
    write_text(root / summary_path, json.dumps(summary, indent=2, sort_keys=True) + "\n")
    return {
        "output_root": output_root.as_posix(),
        "summary_path": summary_path.as_posix(),
        "converted": converted,
        "errors": errors,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a private plain MarkItDown benchmark baseline dump.")
    parser.add_argument("--root", type=Path, required=True, help="Copied pilot vault root.")
    parser.add_argument(
        "--output-root",
        default=DEFAULT_OUTPUT_ROOT.as_posix(),
        help="Relative private output directory; default: _benchmark/plain_markitdown_dump.",
    )
    parser.add_argument(
        "--summary",
        default=DEFAULT_SUMMARY_PATH.as_posix(),
        help="Relative private summary JSON path; default: _benchmark/plain_markitdown_dump-summary.json.",
    )
    parser.add_argument("--include-pdf", action="store_true", help="Also include text-based PDF sources.")
    parser.add_argument("--force", action="store_true", help="Replace an existing output directory.")
    parser.add_argument(
        "--allow-source-checkout-root",
        action="store_true",
        help="Allow writing under the NoeticWeave source checkout; intended only for controlled local tests.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable aggregate JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        output_root = safe_rel_path(args.output_root, "--output-root")
        summary_path = safe_rel_path(args.summary, "--summary")
        summary = create_dump(
            args.root,
            output_root=output_root,
            summary_path=summary_path,
            include_pdf=args.include_pdf,
            force=args.force,
            allow_source_checkout_root=args.allow_source_checkout_root,
        )
    except ValueError as exc:
        print(f"plain markitdown dump: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(
            "plain markitdown dump: "
            f"{summary['converted']} converted, {summary['errors']} error(s); "
            f"output={summary['output_root']} summary={summary['summary_path']}"
        )
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
