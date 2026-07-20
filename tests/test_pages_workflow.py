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


def test_pages_deploy_path_enforces_repository_and_artifact_scans_in_order() -> None:
    workflow = PAGES_WORKFLOW.read_text(encoding="utf-8")
    build = PAGES_BUILD.read_text(encoding="utf-8")

    full_scan = "run: python scripts/no_data_scan.py"
    install = "run: python -m pip install -e ."
    build_demo = 'run: scripts/build_pages_demo.sh "$RUNNER_TEMP/site"'
    assert full_scan in workflow
    assert workflow.index(full_scan) < workflow.index(install) < workflow.index(build_demo)

    assert "examples/ontario-electricity-evidence-vault" in build
    assert "catalog --html --include-content" in build
    assert 'scripts/no_data_scan.py" --paths "$demo_vault/CATALOG.html"' in build
    assert build.index("catalog --html --include-content") < build.index(
        'scripts/no_data_scan.py" --paths "$demo_vault/CATALOG.html"'
    )
    assert "tools/lint_vault.py" in build
    assert 'scripts/build_pages_discovery.py"' in build
    assert 'find "$output_dir" -type f -print0' in build
    assert 'xargs -0 "$python_bin" "$repo_root/scripts/no_data_scan.py" --paths' in build
    assert build.index('scripts/build_pages_discovery.py"') < build.index(
        'find "$output_dir" -type f -print0'
    )
    assert '"document_content_included":true' in build
    assert "Five-minute workspace tour" in build
    assert 'data-prerendered="INDEX.md"' in build
    assert '"$output_dir/sitemap.xml"' in build
    assert '"$output_dir/llms.txt"' in build


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
