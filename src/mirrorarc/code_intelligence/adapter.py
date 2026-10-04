# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small, bounded subprocess adapter for the supported CodeGraph CLI."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import selectors
import signal
import time
from pathlib import Path
from typing import Any

SUPPORTED_VERSION = "1.5.0"
PROVIDER_NAME = "CodeGraph"
PROVIDER_ENV = {
    "DO_NOT_TRACK": "1",
    "CODEGRAPH_TELEMETRY": "0",
    "CODEGRAPH_NO_UPDATE_CHECK": "1",
    "NO_COLOR": "1",
}
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_OUTPUT_LIMIT = 2_000_000


class CodeGraphError(RuntimeError):
    """A bounded and user-safe provider failure."""

    def __init__(
        self,
        message: str,
        *,
        kind: str = "provider-failure",
        command: str = "",
        exit_code: int | None = None,
        stderr: str = "",
    ):
        super().__init__(message)
        self.kind = kind
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "message": str(self),
            "command": self.command,
            "exit_code": self.exit_code,
            "stderr": self.stderr,
        }


def find_codegraph(explicit: str | Path | None = None) -> Path | None:
    """Resolve an operator-provided or PATH-installed executable without installing it."""
    candidate = explicit or os.environ.get("MIRRORARC_CODEGRAPH")
    if candidate:
        path = Path(candidate).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            return path.resolve()
        return None
    resolved = shutil.which("codegraph")
    return Path(resolved).resolve() if resolved else None


def _integer(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _string(value: object) -> str:
    return str(value or "")


def normalize_status(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CodeGraphError("status JSON must be an object", kind="invalid-json-contract")
    pending = value.get("pendingChanges")
    pending = pending if isinstance(pending, dict) else {}
    index = value.get("index")
    index = index if isinstance(index, dict) else {}
    nodes = value.get("nodesByKind")
    nodes = nodes if isinstance(nodes, dict) else {}
    languages = value.get("languages")
    return {
        "initialized": bool(value.get("initialized")),
        "version": _string(value.get("version")),
        "project_path": _string(value.get("projectPath")),
        "index_path": _string(value.get("indexPath")),
        "last_indexed": _string(value.get("lastIndexed")),
        "file_count": _integer(value.get("fileCount")),
        "node_count": _integer(value.get("nodeCount")),
        "edge_count": _integer(value.get("edgeCount")),
        "languages": sorted({_string(item) for item in languages}) if isinstance(languages, list) else [],
        "nodes_by_kind": {str(key): _integer(item) for key, item in sorted(nodes.items())},
        "pending_changes": {
            "added": _integer(pending.get("added")),
            "modified": _integer(pending.get("modified")),
            "removed": _integer(pending.get("removed")),
        },
        "worktree_mismatch": value.get("worktreeMismatch"),
        "index_state": _string(index.get("state")),
        "reindex_recommended": bool(index.get("reindexRecommended")),
    }


def _normalize_symbol(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CodeGraphError("symbol JSON must be an object", kind="invalid-json-contract")
    path = _string(value.get("filePath"))
    if not path:
        raise CodeGraphError("symbol JSON is missing filePath", kind="invalid-json-contract")
    return {
        "provider_id": _string(value.get("id")),
        "kind": _string(value.get("kind")),
        "name": _string(value.get("name")),
        "qualified_name": _string(value.get("qualifiedName") or value.get("name")),
        "path": path,
        "language": _string(value.get("language")),
        "start_line": max(_integer(value.get("startLine")), 1),
        "end_line": max(_integer(value.get("endLine")), _integer(value.get("startLine")), 1),
        "signature": _string(value.get("signature")),
    }


def normalize_query(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise CodeGraphError("query JSON must be a list", kind="invalid-json-contract")
    results: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        symbol = _normalize_symbol(item.get("node"))
        try:
            score = float(item.get("score", 0.0) or 0.0)
        except (TypeError, ValueError):
            score = 0.0
        results.append({**symbol, "score": score})
    return results


def _normalize_related(value: object, key: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not isinstance(value.get(key), list):
        raise CodeGraphError(f"{key} JSON must be an object containing a list", kind="invalid-json-contract")
    items = []
    for item in value[key]:
        if not isinstance(item, dict) or not item.get("filePath"):
            continue
        items.append({
            "name": _string(item.get("name")),
            "kind": _string(item.get("kind")),
            "path": _string(item.get("filePath")),
            "start_line": max(_integer(item.get("startLine")), 1),
        })
    return {"symbol": _string(value.get("symbol")), key: items}


def normalize_impact(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or not isinstance(value.get("affected"), list):
        raise CodeGraphError("impact JSON must contain an affected list", kind="invalid-json-contract")
    affected = []
    for item in value["affected"]:
        if not isinstance(item, dict) or not item.get("filePath"):
            continue
        affected.append({
            "name": _string(item.get("name")),
            "kind": _string(item.get("kind")),
            "path": _string(item.get("filePath")),
            "start_line": max(_integer(item.get("startLine")), 1),
        })
    return {
        "symbol": _string(value.get("symbol")),
        "depth": _integer(value.get("depth")),
        "node_count": _integer(value.get("nodeCount")),
        "edge_count": _integer(value.get("edgeCount")),
        "affected": affected,
    }


def normalize_affected(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CodeGraphError("affected JSON must be an object", kind="invalid-json-contract")
    changed = value.get("changedFiles")
    tests = value.get("affectedTests")
    if not isinstance(changed, list) or not isinstance(tests, list):
        raise CodeGraphError("affected JSON is missing changedFiles or affectedTests", kind="invalid-json-contract")
    return {
        "changed_files": sorted({_string(item) for item in changed if _string(item)}),
        "affected_tests": sorted({_string(item) for item in tests if _string(item)}),
        "total_dependents_traversed": _integer(value.get("totalDependentsTraversed")),
    }


def normalize_files(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise CodeGraphError("files JSON must be a list", kind="invalid-json-contract")
    files = []
    for item in value:
        if not isinstance(item, dict) or not item.get("path"):
            continue
        files.append({
            "path": _string(item.get("path")),
            "language": _string(item.get("language")),
            "symbol_count": _integer(item.get("nodeCount")),
            "size": _integer(item.get("size")),
        })
    return sorted(files, key=lambda item: item["path"])


class CodeGraphAdapter:
    """Invoke only the ordinary, non-daemon CodeGraph project commands MirrorArc supports."""

    def __init__(
        self,
        binary: str | Path | None = None,
        *,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        output_limit: int = DEFAULT_OUTPUT_LIMIT,
    ):
        found = find_codegraph(binary)
        if found is None:
            raise CodeGraphError("local analysis helper was not found", kind="provider-missing")
        self.binary = found
        self.timeout_seconds = timeout_seconds
        self.output_limit = output_limit

    @property
    def environment(self) -> dict[str, str]:
        return {**os.environ, **PROVIDER_ENV}

    def _run(self, args: list[str], *, expect_json: bool = False) -> Any:
        command = [str(self.binary), *args]
        try:
            with subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=self.environment, start_new_session=True,
            ) as child:
                buffers = {"stdout": bytearray(), "stderr": bytearray()}
                deadline = time.monotonic() + self.timeout_seconds
                try:
                    with selectors.DefaultSelector() as selector:
                        selector.register(child.stdout, selectors.EVENT_READ, "stdout")
                        selector.register(child.stderr, selectors.EVENT_READ, "stderr")
                        while selector.get_map():
                            remaining = deadline - time.monotonic()
                            if remaining <= 0:
                                raise subprocess.TimeoutExpired(command, self.timeout_seconds)
                            for key, _ in selector.select(min(remaining, 0.1)):
                                chunk = os.read(key.fd, min(65536, self.output_limit + 1))
                                if not chunk:
                                    selector.unregister(key.fileobj)
                                    continue
                                buffer = buffers[key.data]
                                if len(buffer) + len(chunk) > self.output_limit:
                                    raise CodeGraphError(
                                        "local analysis output exceeded the safety limit",
                                        kind="provider-output-limit", command=" ".join(args[:2]),
                                    )
                                buffer.extend(chunk)
                    child.wait(timeout=max(0.001, deadline - time.monotonic()))
                finally:
                    # Kill the entire session, including descendants holding inherited pipes.
                    try:
                        os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    child.wait()
                result = subprocess.CompletedProcess(
                    command, child.returncode,
                    buffers["stdout"].decode("utf-8", errors="replace"),
                    buffers["stderr"].decode("utf-8", errors="replace"),
                )
        except subprocess.TimeoutExpired as exc:
            raise CodeGraphError(
                f"local analysis timed out after {self.timeout_seconds} seconds",
                kind="provider-timeout",
                command=" ".join(args[:2]),
            ) from exc
        except OSError as exc:
            raise CodeGraphError(
                f"local analysis could not start: {exc}",
                kind="provider-start-failure",
                command=" ".join(args[:2]),
            ) from exc
        if len(result.stdout.encode("utf-8")) > self.output_limit or len(result.stderr.encode("utf-8")) > self.output_limit:
            raise CodeGraphError(
                "local analysis output exceeded the safety limit",
                kind="provider-output-limit",
                command=" ".join(args[:2]),
                exit_code=result.returncode,
            )
        stderr = result.stderr.strip()[:2000]
        if result.returncode != 0:
            raise CodeGraphError(
                "local analysis command failed",
                kind="provider-command-failure",
                command=" ".join(args[:2]),
                exit_code=result.returncode,
                stderr=stderr,
            )
        if not expect_json:
            return {"stdout": result.stdout.strip(), "stderr": stderr, "exit_code": result.returncode}
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise CodeGraphError(
                "local analysis returned invalid JSON",
                kind="invalid-json-contract",
                command=" ".join(args[:2]),
                exit_code=result.returncode,
                stderr=stderr,
            ) from exc

    def version(self) -> str:
        result = self._run(["--version"])
        return str(result["stdout"]).strip().removeprefix("v")

    def status(self, project: Path) -> dict[str, Any]:
        return normalize_status(self._run(["status", str(project), "--json"], expect_json=True))

    def initialize(self, project: Path) -> dict[str, Any]:
        return self._run(["init", str(project)])

    def sync(self, project: Path) -> dict[str, Any]:
        return self._run(["sync", str(project)])

    def ensure_index(self, project: Path) -> dict[str, Any]:
        status = self.status(project)
        if not status["initialized"]:
            self.initialize(project)
            status = self.status(project)
        pending = status["pending_changes"]
        if any(int(pending[key]) for key in ("added", "modified", "removed")) or status["reindex_recommended"]:
            if status["reindex_recommended"]:
                self._run(["index", str(project)])
            else:
                self.sync(project)
            status = self.status(project)
        return status

    def query(self, project: Path, search: str, *, limit: int = 20) -> list[dict[str, Any]]:
        value = self._run(
            ["query", search, "--path", str(project), "--limit", str(limit), "--json"],
            expect_json=True,
        )
        return normalize_query(value)

    def callers(self, project: Path, symbol: str, *, limit: int = 20) -> dict[str, Any]:
        value = self._run(
            ["callers", symbol, "--path", str(project), "--limit", str(limit), "--json"],
            expect_json=True,
        )
        return _normalize_related(value, "callers")

    def callees(self, project: Path, symbol: str, *, limit: int = 20) -> dict[str, Any]:
        value = self._run(
            ["callees", symbol, "--path", str(project), "--limit", str(limit), "--json"],
            expect_json=True,
        )
        return _normalize_related(value, "callees")

    def impact(self, project: Path, symbol: str, *, depth: int = 3) -> dict[str, Any]:
        value = self._run(
            ["impact", symbol, "--path", str(project), "--depth", str(depth), "--json"],
            expect_json=True,
        )
        return normalize_impact(value)

    def affected(self, project: Path, paths: list[str], *, depth: int = 5) -> dict[str, Any]:
        value = self._run(
            ["affected", "--path", str(project), "--depth", str(depth), "--json", "--", *paths],
            expect_json=True,
        )
        return normalize_affected(value)

    def files(self, project: Path) -> list[dict[str, Any]]:
        value = self._run(
            ["files", "--path", str(project), "--format", "flat", "--json"],
            expect_json=True,
        )
        return normalize_files(value)
