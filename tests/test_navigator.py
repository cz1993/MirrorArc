# SPDX-License-Identifier: AGPL-3.0-or-later
from __future__ import annotations

import json
from http import HTTPStatus
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from vaultwright.navigator import (
    DEFAULT_PORT,
    SESSION_COOKIE,
    NavigatorServer,
    render_app,
    render_markdown,
)


def test_default_port_is_ephemeral_to_avoid_browser_origin_reuse() -> None:
    assert DEFAULT_PORT == 0


def test_render_markdown_escapes_html_and_keeps_basic_structure() -> None:
    rendered = render_markdown(
        "---\ntitle: Unsafe\n---\n# Heading\n\n<script>alert('x')</script>\n\n- one\n- two\n"
    )

    assert "<script>" not in rendered
    assert "&lt;script&gt;alert" in rendered
    assert '<h2 id="heading">Heading</h2>' in rendered
    assert "<ul>" in rendered


def test_render_app_script_escapes_payload_and_session_token() -> None:
    page = render_app(
        {"model": {"nodes": [], "trails": []}, "warnings": ["</script>"], "errors": []},
        "</script><script>alert(1)</script>",
    )

    assert page.count("</script>") == 2
    assert "\\u003c/script>" in page
    assert "Local and read-only" in page
    assert 'href="#reader">Skip to document</a>' in page
    assert 'id="local-map"' in page
    assert 'id="rescan"' in page
    assert 'aria-current' in page
    assert "requestVersion !== selectionVersion" in page
    assert "history.replaceState(null, '', location.pathname)" in page
    assert "location.search" not in page
    assert "location.hash" not in page
    assert "response.status === 409" in page
    assert "await rescanNavigation()" in page
    assert "Supporting branch from step" in page
    assert "Use Return to path" in page
    assert "X-Vaultwright-Token" in page


def test_local_server_requires_session_token_and_rejects_cross_origin(tmp_path) -> None:
    (tmp_path / "INDEX.md").write_text(
        "# Local index\n\n<script>alert('not executable')</script>\n",
        encoding="utf-8",
    )
    server = NavigatorServer(tmp_path, 0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = f"http://{host}:{port}"
    token = server.session_token

    try:
        with pytest.raises(HTTPError) as missing:
            urlopen(base + "/", timeout=3)
        assert missing.value.code == HTTPStatus.FORBIDDEN

        with pytest.raises(HTTPError) as missing_api_token:
            urlopen(base + "/api/navigation", timeout=3)
        assert missing_api_token.value.code == HTTPStatus.FORBIDDEN

        with urlopen(base + f"/?token={token}", timeout=3) as response:
            page = response.read().decode("utf-8")
            cookie = response.headers["Set-Cookie"]
            assert response.status == HTTPStatus.OK
            assert "Vaultwright Navigator" in page
            assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
            assert response.headers["Cache-Control"] == "no-store"
            assert cookie.startswith(f"{SESSION_COOKIE}={token};")
            assert "HttpOnly" in cookie
            assert "SameSite=Strict" in cookie

        scrubbed_reload = Request(
            base + "/",
            headers={"Cookie": cookie.split(";", 1)[0]},
        )
        with urlopen(scrubbed_reload, timeout=3) as response:
            assert response.status == HTTPStatus.OK
            assert "Vaultwright Navigator" in response.read().decode("utf-8")

        request = Request(
            base + "/api/document?path=INDEX.md",
            headers={"X-Vaultwright-Token": token},
        )
        with urlopen(request, timeout=3) as response:
            document = response.read().decode("utf-8")
            assert response.status == HTTPStatus.OK
            assert "&lt;script&gt;alert" in document
            assert "<script>alert" not in document

        cross_origin = Request(
            base + "/api/navigation",
            headers={
                "Origin": "https://example.invalid",
                "X-Vaultwright-Token": token,
            },
        )
        with pytest.raises(HTTPError) as rejected:
            urlopen(cross_origin, timeout=3)
        assert rejected.value.code == HTTPStatus.FORBIDDEN

        cross_site = Request(
            base + "/api/navigation",
            headers={
                "Sec-Fetch-Site": "cross-site",
                "X-Vaultwright-Token": token,
            },
        )
        with pytest.raises(HTTPError) as cross_site_rejected:
            urlopen(cross_site, timeout=3)
        assert cross_site_rejected.value.code == HTTPStatus.FORBIDDEN

        hostile_host = Request(
            base + "/api/navigation",
            headers={
                "Host": f"localhost:{port}",
                "X-Vaultwright-Token": token,
            },
        )
        with pytest.raises(HTTPError) as hostile_host_rejected:
            urlopen(hostile_host, timeout=3)
        assert hostile_host_rejected.value.code == HTTPStatus.FORBIDDEN

        traversal = Request(
            base + "/api/document?path=../INDEX.md",
            headers={"X-Vaultwright-Token": token},
        )
        with pytest.raises(HTTPError) as outside:
            urlopen(traversal, timeout=3)
        assert outside.value.code == HTTPStatus.NOT_FOUND
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_local_server_returns_conflict_when_a_document_changes_after_scan(tmp_path) -> None:
    note = tmp_path / "INDEX.md"
    note.write_text("---\nstatus: active\n---\n# Before\n", encoding="utf-8")
    server = NavigatorServer(tmp_path, 0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    token = server.session_token
    note.write_text("---\nstatus: archived\n---\n# After\n", encoding="utf-8")
    request = Request(
        f"http://{host}:{port}/api/document?path=INDEX.md",
        headers={"X-Vaultwright-Token": token},
    )

    try:
        with pytest.raises(HTTPError) as stale:
            urlopen(request, timeout=3)
        assert stale.value.code == HTTPStatus.CONFLICT
        payload = json.loads(stale.value.read().decode("utf-8"))
        assert payload == {
            "error": "document changed after the navigation scan; rescan required"
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
