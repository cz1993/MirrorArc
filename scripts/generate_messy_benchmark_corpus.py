#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generate a synthetic messy corpus for agent-readiness benchmark runs."""
from __future__ import annotations

import argparse
import json
import shlex
import shutil
import sys
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

try:
    import yaml
except ImportError:
    sys.exit("Missing dependency: pip install pyyaml")


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "template"
MODES = ("raw_source_folder", "plain_markitdown_dump", "vaultwright_markdown")
DOMAINS = (
    ("20_market", "market", "market-entry"),
    ("30_customers", "customers", "account-discovery"),
    ("40_delivery", "delivery", "delivery-plan"),
    ("50_operations", "operations", "operating-rhythm"),
    ("60_finance", "finance", "commercial-model"),
)
FAMILIES = ("answer", "reconcile", "update", "audit", "consolidate")
REVIEWED_RESULT_PACK = Path("_benchmark/agent-readiness-results-reviewed.yml")
REVIEWED_SCORE_MATRIX = {
    "raw_source_folder": {
        "answer": (1, 1),
        "reconcile": (1, 2),
        "update": (0, 3),
        "audit": (1, 1),
        "consolidate": (0, 3),
    },
    "plain_markitdown_dump": {
        "answer": (2, 0),
        "reconcile": (1, 1),
        "update": (0, 3),
        "audit": (1, 1),
        "consolidate": (0, 3),
    },
    "vaultwright_markdown": {
        "answer": (2, 0),
        "reconcile": (2, 0),
        "update": (2, 0),
        "audit": (2, 0),
        "consolidate": (2, 0),
    },
}


def protected_targets() -> set[Path]:
    return {
        Path("/").resolve(),
        Path.home().resolve(),
        Path.cwd().resolve(),
        ROOT.resolve(),
        ROOT.parent.resolve(),
    }


def safe_target(path: Path) -> Path:
    target = path.expanduser().resolve()
    if target == ROOT or ROOT in target.parents:
        raise ValueError("target must be outside the Vaultwright source checkout")
    if target in protected_targets():
        raise ValueError(f"target is too broad to replace safely: {target}")
    if len(target.parts) < 3:
        raise ValueError(f"target is too broad to replace safely: {target}")
    return target


def ensure_target(target: Path, *, force: bool) -> None:
    if target.exists():
        if not force:
            raise ValueError(f"target already exists: {target}; use --force to replace it")
        if target.is_file() or target.is_symlink():
            target.unlink()
        else:
            shutil.rmtree(target)
    shutil.copytree(TEMPLATE, target)


def write_docx(path: Path, *, title: str, paragraphs: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(
        f"<w:p><w:r><w:t>{escape(paragraph)}</w:t></w:r></w:p>"
        for paragraph in [title, *paragraphs]
    )
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}</w:body>"
        "</w:document>"
    )
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                '<Default Extension="xml" ContentType="application/xml"/>'
                '<Override PartName="/word/document.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                "</Types>"
            ),
        )
        archive.writestr(
            "_rels/.rels",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
                'Target="word/document.xml"/>'
                "</Relationships>"
            ),
        )
        archive.writestr("word/document.xml", document)


def note_frontmatter(title: str, domain: str) -> str:
    return (
        "---\n"
        f"title: {title}\n"
        "type: note\n"
        "status: draft\n"
        f"domain: {domain}\n"
        "created: 2026-07-03\n"
        "updated: 2026-07-03\n"
        "---\n"
    )


def source_rel(index: int) -> Path:
    folder, _domain, topic = DOMAINS[index % len(DOMAINS)]
    account = f"synthetic-account-{index % 17:02d}"
    return Path(folder) / account / f"2026-q{index % 4 + 1}_{topic}_{index:03d}.docx"


def source_paragraphs(index: int) -> list[str]:
    folder, domain, topic = DOMAINS[index % len(DOMAINS)]
    account = f"Synthetic Account {index % 17:02d}"
    quarter = f"2026-Q{index % 4 + 1}"
    return [
        f"Domain: {domain}; folder: {folder}; topic: {topic}.",
        f"{account} has a {quarter} operating question with one intentionally overlapping fact.",
        f"Evidence marker VW-MESSY-{index:03d} should be cited when this source is used.",
        "This synthetic file contains no personal data, confidential client data, or real company facts.",
    ]


def write_source(target: Path, index: int) -> str:
    rel = source_rel(index)
    title = f"Synthetic {rel.stem.replace('_', ' ').title()}"
    write_docx(target / rel, title=title, paragraphs=source_paragraphs(index))
    return rel.as_posix()


def write_curated(target: Path, index: int) -> str:
    folder, domain, topic = DOMAINS[index % len(DOMAINS)]
    rel = Path(folder) / f"synthetic-{topic}-hub-{index:03d}.md"
    title = f"Synthetic {topic.replace('-', ' ').title()} Hub {index:03d}"
    body = (
        note_frontmatter(title, domain)
        + f"\n# {title}\n\n"
        + f"- Consolidates recurring {domain} observations for synthetic account work.\n"
        + f"- Related marker: VW-MESSY-CURATED-{index:03d}.\n"
        + "- Prefer updating this note before creating a duplicate hub.\n"
    )
    path = target / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return rel.as_posix()


def mirror_rel(source: str) -> str:
    return (Path("_mirrors") / Path(source)).with_suffix(".md").as_posix()


def plain_dump_rel(source: str) -> str:
    return (Path("_benchmark/plain_markitdown_dump") / Path(source)).with_suffix(".md").as_posix()


def write_plain_dump(target: Path, source: str, index: int) -> str:
    rel = plain_dump_rel(source)
    path = target / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(
        [
            f"# Plain conversion dump for {source}",
            "",
            *source_paragraphs(index),
            "",
            "No Vaultwright manifest identity, lifecycle state, or curated hub context is attached.",
        ]
    )
    path.write_text(text + "\n", encoding="utf-8")
    return rel


def spread(values: list[str], start: int, count: int) -> list[str]:
    if not values:
        return []
    out = []
    for offset in range(count):
        out.append(values[(start + offset) % len(values)])
    return out


def task_pack(source_paths: list[str], curated_paths: list[str]) -> dict:
    specs = {
        "answer": "Which source-backed account facts are safe to answer from this corpus?",
        "reconcile": "Which overlapping sources disagree or need human reconciliation?",
        "update": "If a source changes, which mirrors and curated notes need review?",
        "audit": "What evidence trail supports a recommendation across this messy corpus?",
        "consolidate": "Where should a new related fact live without creating duplicate notes?",
    }
    tasks = []
    for index, family in enumerate(FAMILIES):
        selected_sources = spread(source_paths, index * 7, 5)
        selected_curated = spread(curated_paths, index * 3, 3)
        tasks.append(
            {
                "id": f"messy-{family}",
                "family": family,
                "prompt": specs[family],
                "source_paths": selected_sources,
                "generated_mirror_paths": [mirror_rel(source) for source in selected_sources],
                "curated_paths": selected_curated if family in {"update", "consolidate"} else [],
                "success_criteria": [
                    "uses only declared source, mirror, or curated paths as evidence",
                    "cites relative vault paths for material claims",
                    "flags unknowns and human-review needs instead of guessing",
                ],
            }
        )
    return {
        "schema_version": 1,
        "corpus": "messy-synthetic-consulting-corpus",
        "description": "Synthetic 200-file messy benchmark task pack; generated by scripts/generate_messy_benchmark_corpus.py.",
        "comparison_modes": list(MODES),
        "scoring": {
            "scale": "0-2",
            "zero": "wrong, uncited, unsafe, or not actionable",
            "one": "partially correct but missing caveats, citations, or audit/update evidence",
            "two": "correct, source-backed, and operationally useful",
        },
        "tasks": tasks,
    }


def result_scaffold(tasks: list[dict]) -> dict:
    results = []
    for task in tasks:
        for mode in MODES:
            results.append(
                {
                    "task_id": task["id"],
                    "mode": mode,
                    "score": None,
                    "reviewer_corrections": None,
                    "elapsed_seconds": None,
                    "cited_source_paths": [],
                    "cited_generated_mirror_paths": [],
                    "privacy_or_provenance_violation": False,
                    "prompt_safety_reviewed": None,
                    "prompt_safety_violation": None,
                }
            )
    return {
        "schema_version": 1,
        "corpus": "messy-synthetic-consulting-corpus",
        "results": results,
    }


def reviewed_result_pack(tasks: list[dict]) -> dict:
    results = []
    for task in tasks:
        family = str(task.get("family", "")).strip()
        if family not in FAMILIES:
            raise ValueError(f"cannot score unknown benchmark family: {family or '(missing)'}")
        sources = [str(path) for path in task.get("source_paths", []) if str(path).strip()]
        mirrors = [str(path) for path in task.get("generated_mirror_paths", []) if str(path).strip()]
        for mode in MODES:
            score, corrections = REVIEWED_SCORE_MATRIX[mode][family]
            entry = {
                "task_id": task["id"],
                "mode": mode,
                "score": score,
                "reviewer_corrections": corrections,
                "elapsed_seconds": None,
                "cited_source_paths": sources[:1] if score > 0 else [],
                "cited_generated_mirror_paths": mirrors[:1] if score > 0 and mode == "vaultwright_markdown" else [],
                "privacy_or_provenance_violation": False,
                "prompt_safety_reviewed": True,
                "prompt_safety_violation": False,
            }
            results.append(entry)
    return {
        "schema_version": 1,
        "corpus": "messy-synthetic-consulting-corpus",
        "results": results,
    }


def write_run_sheet(target: Path, summary: dict) -> None:
    quoted_target = shlex.quote(str(target))
    text = f"""# Messy Synthetic Benchmark Run Sheet

This vault contains a synthetic messy consulting corpus. It is generated data, not a customer
workspace.

## Corpus

- Corpus files: {summary["corpus_files"]}
- Office-like source files: {summary["source_files"]}
- Curated markdown notes: {summary["curated_files"]}
- Plain conversion dump files: {summary["plain_dump_files"]}
- Benchmark task/mode slots: {summary["result_slots"]}

## Commands

```bash
vaultwright --root {quoted_target} sync
vaultwright --root {quoted_target} benchmark --require-generated
vaultwright --root {quoted_target} benchmark --worksheet > {quoted_target}/_benchmark/agent-readiness-worksheet.md
```

After the same agent answers each task in each mode, copy
`_benchmark/agent-readiness-results-scaffold.yml` to a private result pack, fill the aggregate
scores, and validate it with:

```bash
vaultwright --root {quoted_target} benchmark \\
  --results _benchmark/agent-readiness-results-scaffold.yml \\
  --require-results \\
  --require-citations \\
  --require-prompt-safety
```
"""
    (target / "_benchmark" / "MESSY_BENCHMARK_RUN.md").write_text(text, encoding="utf-8")


def build_corpus(target: Path, *, files: int, force: bool) -> dict:
    if files < 20:
        raise ValueError("--files must be at least 20")
    target = safe_target(target)
    ensure_target(target, force=force)
    benchmark_dir = target / "_benchmark"
    benchmark_dir.mkdir(parents=True, exist_ok=True)

    source_count = max(5, int(files * 0.6))
    curated_count = files - source_count
    source_paths = [write_source(target, index) for index in range(source_count)]
    curated_paths = [write_curated(target, index) for index in range(curated_count)]
    plain_paths = [write_plain_dump(target, source, index) for index, source in enumerate(source_paths)]

    tasks = task_pack(source_paths, curated_paths)
    task_path = target / "_meta" / "agent-readiness-tasks.yml"
    task_path.write_text(yaml.safe_dump(tasks, sort_keys=False, allow_unicode=False), encoding="utf-8")
    result_path = benchmark_dir / "agent-readiness-results-scaffold.yml"
    result_path.write_text(
        yaml.safe_dump(result_scaffold(tasks["tasks"]), sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )
    summary = {
        "target": str(target),
        "corpus_files": files,
        "source_files": len(source_paths),
        "curated_files": len(curated_paths),
        "plain_dump_files": len(plain_paths),
        "task_pack": task_path.relative_to(target).as_posix(),
        "tasks": len(tasks["tasks"]),
        "comparison_modes": list(MODES),
        "result_scaffold": result_path.relative_to(target).as_posix(),
        "result_slots": len(tasks["tasks"]) * len(MODES),
    }
    (benchmark_dir / "messy-corpus-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_run_sheet(target, summary)
    return summary


def write_reviewed_result_pack(target: Path) -> Path:
    task_path = target / "_meta" / "agent-readiness-tasks.yml"
    task_data = yaml.safe_load(task_path.read_text(encoding="utf-8")) or {}
    tasks = task_data.get("tasks", [])
    if not isinstance(tasks, list):
        raise ValueError("generated task pack is missing tasks")
    result_path = target / REVIEWED_RESULT_PACK
    result_path.write_text(
        yaml.safe_dump(reviewed_result_pack(tasks), sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )
    return result_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a synthetic messy benchmark corpus.")
    parser.add_argument("--target", type=Path, required=True, help="Output vault path outside the source checkout.")
    parser.add_argument("--files", type=int, default=200, help="Synthetic corpus file count; default: 200.")
    parser.add_argument("--force", action="store_true", help="Replace an existing target directory.")
    parser.add_argument(
        "--write-reviewed-results",
        action="store_true",
        help="Write a synthetic reviewed no-content result pack for dogfood scoring.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable summary JSON only.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = build_corpus(args.target, files=args.files, force=args.force)
        if args.write_reviewed_results:
            result_path = write_reviewed_result_pack(Path(summary["target"]))
            summary["reviewed_result_pack"] = result_path.relative_to(Path(summary["target"])).as_posix()
    except ValueError as exc:
        print(f"messy benchmark corpus: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        reviewed_line = (
            f"\n                  reviewed results: {summary['reviewed_result_pack']}"
            if "reviewed_result_pack" in summary
            else ""
        )
        print(
            textwrap.dedent(
                f"""
                messy benchmark corpus: wrote {summary['corpus_files']} files to {summary['target']}
                  sources: {summary['source_files']}
                  curated: {summary['curated_files']}
                  plain dump: {summary['plain_dump_files']}
                  tasks: {summary['tasks']} across {len(summary['comparison_modes'])} modes{reviewed_line}
                  next: vaultwright --root {summary['target']} sync
                """
            ).strip()
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
