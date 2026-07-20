#!/usr/bin/env sh
# SPDX-License-Identifier: AGPL-3.0-or-later
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 OUTPUT_DIRECTORY" >&2
  exit 2
fi

output_dir=$1
if [ -z "$output_dir" ] || [ "$output_dir" = "/" ]; then
  echo "refusing unsafe output directory: $output_dir" >&2
  exit 2
fi

repo_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
demo_source="$repo_root/examples/ontario-electricity-evidence-vault"
python_bin=${PYTHON:-python3}
temp_root=$(mktemp -d)
demo_vault="$temp_root/ontario-electricity-evidence-vault"

cleanup() {
  rm -rf "$temp_root"
}
trap cleanup EXIT HUP INT TERM

cp -R "$demo_source" "$demo_vault"

"$python_bin" "$demo_vault/tools/mirrorarc.py" plan
"$python_bin" "$demo_vault/tools/mirrorarc.py" sync
"$python_bin" "$demo_vault/tools/mirrorarc.py" status
"$python_bin" "$demo_vault/tools/mirrorarc.py" catalog --html --include-content
"$python_bin" "$demo_vault/tools/lint_vault.py"
"$python_bin" "$repo_root/scripts/no_data_scan.py" --paths "$demo_vault/CATALOG.html"

grep -q '"document_content_included":true' "$demo_vault/CATALOG.html"
grep -q 'Five-minute workspace tour' "$demo_vault/CATALOG.html"

mkdir -p "$output_dir"
"$python_bin" "$repo_root/scripts/build_pages_discovery.py" \
  "$demo_vault/CATALOG.html" \
  "$output_dir" \
  --base-url "https://cz1993.github.io/MirrorArc/"

find "$output_dir" -type f -print0 | xargs -0 "$python_bin" "$repo_root/scripts/no_data_scan.py" --paths

grep -q 'data-prerendered="INDEX.md"' "$output_dir/index.html"
grep -q '<link rel="canonical" href="https://cz1993.github.io/MirrorArc/">' "$output_dir/index.html"
grep -q 'https://cz1993.github.io/MirrorArc/documents/' "$output_dir/sitemap.xml"
grep -q '# MirrorArc' "$output_dir/llms.txt"

echo "pages demo: wrote crawlable site to $output_dir"
