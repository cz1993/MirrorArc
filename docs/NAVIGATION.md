# Vaultwright Navigator

Vaultwright Navigator is the first-party, read-only human interface for locating and reading local
Markdown without requiring Obsidian. It scans the current vault when loaded, keeps source and
mirror files in place, and exposes only a loopback HTTP server.

## Run It

```bash
vaultwright --root /path/to/vault navigate --check
vaultwright --root /path/to/vault navigate
```

The check command validates the collection model and authored trails without starting a server.
The second command prints a launch URL containing a new unguessable token and serves until
interrupted. Use that exact URL for the first page. The browser immediately removes the token from
the address bar and route history, then uses a same-site, HTTP-only session cookie for page reloads
and the in-page token in an `X-Vaultwright-Token` header for document/API reads. The token is valid
only while that server process runs.
The operating system selects a fresh loopback port by default so the browser origin is not reused
predictably. `--port <number>` is available for controlled debugging, but a previously used fixed
origin can retain browser state such as a service worker; prefer the default.

Navigator scans when the page loads. Use **Rescan** after files or trails change; it refreshes the
ephemeral model through the guarded API while preserving the current in-memory document route.
Document paths, trail position, and recent-document history are not written into the browser URL
or local storage. A full page reload returns to the default start rather than persisting that state.

## Authored Reading Trails

`_meta/navigation.yml` is optional. Without it, Navigator still supports title/path filtering,
local reading, inbound links, and outbound links. The filter is not indexed full-text search. Add
trails when a collection has a useful reading order:

```yaml
schema_version: 1
trails:
  - id: first-review
    title: First review
    goal: Understand the source boundary before reviewing the operating decision.
    audience: New reviewers
    steps:
      - path: INDEX.md
        why: Orient to the collection and its governance rules.
      - path: 10_governance/Source Notes.md
        why: Establish which records are authoritative before reading derived guidance.
      - path: 40_delivery/Decision Guide.md
        why: Apply the source boundary to the decision workflow.
```

Trail IDs must be unique. Every step path must name a Markdown document already visible to the
active profile, remain inside the vault, and include a human-written `why`. Missing, ambiguous,
unsafe, and symlink-escaping paths fail `navigate --check`.

## What Navigator Does Not Do

- It does not infer an authoritative reading order from filenames or an opaque model.
- It does not write note bodies, progress files, links, or route suggestions.
- It does not replace the metadata-only `CATALOG.md` and `CATALOG.html` handoff artifacts.
- It does not create the later evidence index, global graph, MCP exploration tool, or context pack.
- It does not make generated mirrors authoritative; source paths, lifecycle state, and human review
  remain governed by the existing profile and manifest contracts.

## Bounded Local Map

Selecting a document redraws an interactive one-hop map in the browser's HTML Canvas. The current
document stays in the center, with up to four inbound and four outbound linked documents visible;
selecting a visible neighbor opens it and redraws the neighborhood. This is deliberately a local
context view, not a whole-vault graph.

The complete inbound and outbound sets remain available immediately below the Canvas as ordinary
link lists. Those lists are the keyboard-operable and screen-reader-friendly equivalent of the
visual map, and they also expose neighbors omitted by the visual cap. The Canvas is an ephemeral
browser rendering: it does not create an Obsidian `.canvas` file, persist coordinates, or add a
graph index.

## Security Boundary

Navigator binds to `127.0.0.1`, generates a new session token for every launch, and accepts the
initial page only through the tokenized launch URL. API reads require the same token in an
`X-Vaultwright-Token` header. The server requires the exact loopback `Host`, rejects a mismatched
`Origin` and `Sec-Fetch-Site: cross-site`, sends a restrictive Content Security Policy, disables
caching, and HTML-escapes Markdown instead of executing embedded HTML. Document requests are
revalidated against the current navigation model and vault boundary. A revision mismatch returns a
conflict and causes the page to rescan before presenting the changed body beside trust metadata.
Control/runtime directories and directories named `private` or `secrets` are excluded even when a
profile root would otherwise include them. The proof also refuses individual Markdown files above
16 MiB, navigation configuration above 1 MiB, more than 5,000 documents, more than 20,000 link
occurrences in one note, more than 100,000 link occurrences overall, more than 10,000 distinct link
diagnostics, or a scan above 256 MiB; narrow the active profile roots rather than raising those
bounds casually.

These controls reduce exposure from other local or browser origins; they are not multi-user
authentication. Treat the printed launch URL as sensitive for the life of the process, and do not
expose the loopback port through a tunnel or reverse proxy. Hosted access remains outside this
proof slice.

## Proof Status

The bounded implementation slice exists and is covered by synthetic contract and server-safety
tests. Its product value is not validated. Stage 3 remains incomplete until a permission-cleared
external corpus completes the full protocol in `docs/VALIDATION_GATE.md`; Navigator-only or
synthetic results cannot close that gate.

## Pilot Measures

Evaluate navigation with tasks rather than graph aesthetics:

- time to first correct document;
- correct-document success without search;
- authored-trail completion and abandonment;
- wrong turns and backtracking;
- ability to explain why one document follows another;
- recognition of source authority, staleness, or supersession;
- Obsidian-free task completion; and
- performance for first-time versus experienced users.
