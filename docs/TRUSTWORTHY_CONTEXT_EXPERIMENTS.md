# Trustworthy Context — bounded experiment results

Measured locally on macOS arm64, Python 3.11.15, September 18–19, 2026. These are small synthetic
experiments, not production, Linux, model-answer-quality, or comparative statistical proof.
Raw scripts, stdout/stderr and JSON: `/tmp/mirrorarc-tc-upstream`. Preserve that directory for review.

## CodeGraph: retain 1.5.0

The [official 1.6.0 release](https://github.com/colbymchenry/codegraph/releases/tag/v1.6.0)
and its installer were inspected. Both Darwin arm64 archives were checked against the respective
release SHA256SUMS before disposable extraction. No agent installer or global install ran.

| Version | Archive SHA-256 | Comparison elapsed | Result |
| --- | --- | --- | --- |
| 1.5.0 | cf5ee435a6e44d097b2f98f2b7b8b9422bb1094844404efed82519c5da1af2cf | 4.206 s | contracts passed |
| 1.6.0 | 1c73033512d55f67be04717e81532e8beaf7be6fb8531f51a179fa23064ad480 | 4.800 s | contracts passed |

`compare_codegraph.py` uses the same existing synthetic repository for version/init/status,
query, callers/callees, impact, affected tests, files, added-symbol/edit, rename, delete, two
cache rebuilds, and malformed-command failure. Both returned three query hits, two caller hits,
three impact hits, and an empty provider affected-test list for this request. MirrorArc's
symbol-impact test candidates are labeled candidates; the provider did not prove them.
One timing per version does not establish a performance difference. No concrete benefit was
shown, so the pin remains 1.5.0. Final wheel smoke additionally exercised the actual adapter.

Wrappers set `DO_NOT_TRACK=1`, `CODEGRAPH_TELEMETRY=0`, and
`CODEGRAPH_NO_UPDATE_CHECK=1`, and use macOS `sandbox-exec` to deny network and writes under
`/Users/cz`. These comparisons demonstrate offline execution; environment flags alone would
not prove that telemetry was suppressed. Download/extraction initially failed on the older
system Python's tar API; one retry using Python 3.11 succeeded. Both logs are retained.

The retained script uses fixed disposable paths and refuses an existing fixture directory. For a rerun, first copy the experiment directory to a new location and change its `root` to that location; omit `fixture-1.5.0` and `fixture-1.6.0` from the copy. The original invocation was:

```sh
/tmp/mirrorarc-tc-venv/bin/python /tmp/mirrorarc-tc-upstream/compare_codegraph.py
```

## Docling: no adoption

[Docling](https://github.com/docling-project/docling) 2.129.0 was installed only in
`/tmp/mirrorarc-tc-docling`. Its code is MIT-licensed; model assets have separate licenses and
were neither downloaded nor evaluated. MarkItDown 0.1.7 remains the converter.
`create_pdfs.py` generated three one-page synthetic documents: a table, two columns, and a raster
scan. The table rendering was inspected. No private document was used or transmitted.

| Input | MarkItDown output | Time / peak RSS | Docling default result | Time / peak RSS |
| --- | --- | --- | --- | --- |
| table | 204 characters; all table values recovered | 0.662 s / 149,929,984 bytes | missing RapidOCR artifacts | 3.869 s / 405,635,072 bytes |
| columns | 222 characters; reading order interleaves columns | 0.339 s / 149,929,984 bytes | missing RapidOCR artifacts | 2.009 s / 400,064,512 bytes |
| scan | zero characters; extraction failure despite converter success | 0.331 s / 149,553,152 bytes | missing RapidOCR artifacts | 2.106 s / 405,536,768 bytes |

One bounded hypothesis was tested: disable OCR and use backend text on the table. It still
failed because `docling-project/docling-layout-heron` was absent (5.509 s, 509,034,496-byte peak
RSS). No further retry/model download/integration was attempted. The comparison wrapper exits
successfully when it records an extraction error; inspect each JSON `status`, not only the
wrapper return code. Source/page anchor arrays were empty for both tools. These runs establish
neither a Docling quality advantage nor page-citation support. Errors and dependency/network
requirements are the measured outcome. MarkItDown's scan and column limitations remain explicit.

The extraction processes used `HF_HUB_OFFLINE=1`, telemetry suppression and an OS deny-network
sandbox. No model endpoint, model download, or paid inference was used. The original extraction invocations (use a new output root to retain prior evidence):

```sh
/tmp/mirrorarc-tc-venv/bin/python /tmp/mirrorarc-tc-upstream/create_pdfs.py
/tmp/mirrorarc-tc-venv/bin/python /tmp/mirrorarc-tc-upstream/compare_docs.py
```

PageIndex remains a design reference. It was not run or integrated. Promptfoo was not needed;
no provider framework, MCP dependency, daemon, vector database, or additional lifecycle authority
was introduced.
