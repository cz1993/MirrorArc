# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGES_WORKFLOW = ROOT / ".github" / "workflows" / "pages.yml"
PAGES_BUILD = ROOT / "scripts" / "build_pages_demo.sh"


def test_pages_workflow_deploys_only_from_main_or_manual_dispatch() -> None:
    text = PAGES_WORKFLOW.read_text(encoding="utf-8")

    assert "branches: [main]" in text
    assert "workflow_dispatch:" in text
    assert "pull_request:" not in text
    assert "persist-credentials: false" in text
    assert "scripts/build_pages_demo.sh" in text
    assert "actions/configure-pages@v5" in text
    assert "actions/upload-pages-artifact@v4" in text
    assert "actions/deploy-pages@v4" in text
    assert "pages: write" in text
    assert "id-token: write" in text
    assert "environment:" in text
    assert "name: github-pages" in text


def test_pages_build_is_bounded_to_the_public_demo_and_scanned() -> None:
    text = PAGES_BUILD.read_text(encoding="utf-8")

    assert "examples/ontario-electricity-evidence-vault" in text
    assert "catalog --html --include-content" in text
    assert "scripts/no_data_scan.py" in text
    assert "tools/lint_vault.py" in text
    assert '"document_content_included":true' in text
    assert "Five-minute workspace tour" in text
    assert '"$output_dir/index.html"' in text
    assert '"$output_dir/.nojekyll"' in text


def test_public_docs_link_to_the_hosted_demo_and_keep_private_vaults_local() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    quickstart = (ROOT / "docs" / "quickstart.md").read_text(encoding="utf-8")
    security = (ROOT / "docs" / "SECURITY_MODEL.md").read_text(encoding="utf-8")
    normalized_security = " ".join(security.split())

    demo_url = "https://cz1993.github.io/MirrorArc/"
    assert demo_url in readme
    assert demo_url in quickstart
    assert "public demo corpus" in normalized_security
    assert "private or proprietary vault" in normalized_security
