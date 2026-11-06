# Reads

Implementation: independent collection/capture/search core, CLI, Control Center
view, and an unpacked Edge extension. No browser history ingestion, bookmark
cleanup artifacts, automatic membership classification, or historical-data
migration. Nothing installs or connects to your browser automatically.

## Local Development

From the repository root:

```sh
uv sync --project agb --extra dev
load-node
pnpm --dir web-app/frontend install --frozen-lockfile
pnpm --dir web-app/frontend build
PYTHONPATH=agb/src agb/.venv/bin/python -m ab serve --port 4750
```

Open `http://127.0.0.1:4750`, then Reads. Search, collection coverage, capture
errors/retries, original passages, notes, privacy settings, and source identities
are available there. Empty state is real: the app does not seed example readings.
The Sources tab also previews and accepts adapter JSON snapshots for development.

This checkout is separate from the installed Control Center. Building or running
it does not update that installation, restart its service, or remove old data.

## Edge Connection (macOS)

1. In `edge://extensions`, enable developer mode and load the repository's
   `browser/reads-edge` directory as an unpacked extension.
2. Copy its extension ID and explicitly register this checkout's native host:

   ```sh
   agb/.venv/bin/agb reads install-edge-host <extension-id>
   ```

3. Open the extension popup, select the intended folder by ID, preview its
   complete subtree, and accept it. Only that selected subtree is synced.
4. Inspect the collection in Reads and explicitly capture pending public pages.

The host is restricted to the extension ID and accepts only complete Edge
snapshots and rendered HTML for an existing active saved URL. It does not expose
a local HTTP listener, arbitrary commands, or a general URL-fetch endpoint.
The extension stores its installation/profile identity, selected folder ID, and
pending snapshot locally. Bookmark events and startup/one-minute reconciliation
produce complete snapshots. A pending snapshot is retained until acknowledged.
Failed/partial reads never establish absence. Selecting a different folder
excludes the old selection for that profile without deleting browser bookmarks.

The extension requests bookmarks, storage, alarms, native messaging, and
user-triggered activeTab/scripting access, not history or broad site access.
Rendered-page capture is an explicit popup action for a saved active tab, is
bounded to 800 KB HTML, and resets that reading to local-only atomically. It never
sends browser cookies to the public fetcher. Capture/sync inside a real Edge
profile still needs user acceptance testing; this implementation was tested with
synthetic records and mocked browser events only.

## CLI

```sh
agb reads sources
agb reads sync synthetic-snapshot.json --dry-run
agb reads sync synthetic-snapshot.json
agb reads capture --pending
agb reads capture --document <document-id>
agb reads status
agb reads search "realtime session creation" --local-only
agb reads policy <document-id> --note "My note" --allow-cloud
agb reads search "realtime session creation" --provider decision --allow-cloud
agb reads search "session creation" --provider llm --allow-cloud --constraints "Not Azure"
agb reads evaluate private-cases.json
```

`sync` accepts the source-independent contract, not an old cleanup export:

```json
{
  "source_id": "synthetic",
  "profile_id": "test-profile",
  "folder_id": "reads-17",
  "revision": 1,
  "complete": true,
  "items": [{
    "item_id": "bookmark-42",
    "url": "https://example.org/article?version=1#section",
    "title": "An original title",
    "folder_path": "Reads/Reference",
    "saved_at": null
  }]
}
```

Revisions increase per profile. Repeating a snapshot is idempotent; reusing its
revision with different content is rejected. Exact URLs are retained, including
identity parameters and anchors. Memberships share documents only for identical
URLs. Removing one membership does not exclude a document with another active
membership. Inactive local content is retained; automatic retention expiry and a
purge command are not implemented.

## Capture And Search

Public capture supports HTML and plain text using Trafilatura. Unsupported
formats, authentication failures, unavailable pages, extraction errors, and
size/time limits remain visible. DNS addresses are validated and pinned for each
request; all redirects are revalidated. Private/loopback/link-local destinations,
embedded credentials, unusual ports, cookies, and unbounded responses are blocked.
Jobs have attempt counts, retry backoff, and expiring leases. A failed refresh
retains the last good passages. Status reports capture failures separately from
available content coverage.

FTS5 searches active titles, exact URLs, notes, headings, and original passages.
Title-only matches are explicitly metadata-only, without invented supporting
excerpts. Local search never calls a model; constraints require model assessment
and remain explicitly unverified on lexical-only candidates.

Assisted search assesses every cloud-approved document, splitting long captures
into bounded packs with explicit unassessed coverage. Calls share a configurable
12-call/120-second starting budget. Structured LLM output must reference real IDs
and exact stored quotes. Decision questions separately assess relevance,
sufficiency, constraint violation, and passage choice. Failure/budget exhaustion
is visible; fallback is lexical-only, not a silently substituted model. Model
categories are provisional, not calibrated confidence guarantees. Retrieval uses
all captured passages; extraction completeness relative to the rendered page is
not established automatically. Publication/modified-date extraction, hierarchical
heading paths, local embeddings, and automatic freshness policy remain future
work.

## Decision Deployment Configuration

No deployed model was accessed during implementation. The public model card does
not establish the deployment's endpoint/schema. The configurable transport must
be matched to the deployment's generated inference example before enabling it.
It deliberately does not assume OpenAI Decisions or chat-completions compatibility.

Set configuration in `~/.agb/.env` (the tracked `.env.example` lists the names):

- `AB_READS_DECISION_ENDPOINT`: complete HTTPS inference URL, including API version.
- `AB_READS_DECISION_DEPLOYMENT`: deployment identifier.
- `AB_READS_DECISION_API_KEY`: optional key; otherwise Entra ID is used.
- `AB_READS_DECISION_REQUEST_TEMPLATE`: JSON matching the **verified native schema**.
  Exact string values `$context`, `$question`, `$options`, and `$deployment` are
  replaced with the evidence JSON string, rubric question, option-string list,
  and deployment ID. This is not a claim that any particular field names work.
- `AB_READS_DECISION_RESPONSE_PATH`: dot-separated path to the native response's
  complete `{option: probability}` object; numeric segments index arrays.

If the deployed schema cannot represent questions/options this way, or returns
scores in a different structure, its provider mapping needs a corresponding
adapter change. An endpoint/key alone does not verify schema compatibility.
Unknown/missing options, invalid probabilities, provider errors, and refusals are
visible failures. Synthetic tests exercise the mapping, not live inference.
The structured LLM baseline uses the existing Azure OpenAI endpoint/deployment;
the Reads adapter supports reasoning-model completion-token parameters without
changing the Text agent's client.

Configuration does not grant content approval. Every reading starts local-only.
Cloud search additionally requires its saved consent and the explicit cloud
search mode. The local-only override always wins. No model is allowed tools or
authority from captured page text. No raw provider responses or content are
written to application logs. Evaluation returns native responses locally for
inspection; treat that output as private.

## Verification

```sh
PYTHONPATH=agb/src:web-app agb/.venv/bin/python -m pytest agb/tests web-app/tests -q
load-node
node --test browser/reads-edge/test-background.mjs
pnpm --dir web-app/frontend test:ui
pnpm --dir web-app/frontend build
pnpm --dir web-app/frontend lint
```

UI tests use installed Google Chrome and synthetic API responses on desktop/mobile.
API/core tests use temporary databases and no live cloud requests. Real-bookmark
capture coverage, native-host packaging/permissions in Edge, Decision inference,
pricing, and the agreed private 20-query/6-no-match quality gates remain
unverified. Do not equate passing synthetic tests with those acceptance gates.

Evaluation input is a local JSON array of `{ "query": "...", "expected_ids":
["document-id"], "constraints": "..." }` cases. Use an empty ID list for no-match
cases. The runner reports top-three outcomes, provider mode, timing, call/coverage
diagnostics, and native responses. Partial searches and unavailable requested
assessors cannot pass an assessment case. Keep private cases outside the repository.