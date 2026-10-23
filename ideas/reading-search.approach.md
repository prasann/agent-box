# Reading Search Agent - Implementation Plan

Status: proposed implementation plan, not implemented.
Date: 2026-10-23.
Working command name: `agb reads`.

## Goal

Find the right saved reading from an imperfect recollection. Search quality and
evidence matter more than latency. Search volume is low, so spend model effort
at query time rather than classifying everything during ingestion.

The browser is the source of truth for what belongs in Reads. This is a new agent,
not a continuation of the retired browser-history classification pipeline.

## Starting Point

FindTab's implementation, CLI registration, tests, configuration, xbar actions,
and old proposal have been removed from this repository. Reads is not implemented
yet. The separately installed Control Center and historical local data remain
untouched; repository cleanup is not a deployment or data purge.

Bookmark cleanup is complete and is a separate, one-time activity. Its review
page, decision files, exports, and removal backups are not agent dependencies.
The user has deleted the cleanup exports; do not require or recreate them.

The last reviewed collection contained nine Reads. This is historical context,
not a hardcoded collection size or a guarantee about the current browser state.
The live selected Reads subtree is authoritative for membership and counts.

Select the current Reads folder by browser bookmark ID and profile identity,
not its old exported path or every folder named Reads. Normal bookmarks outside
that selected subtree remain outside the agent's collection.

## Independent Agent Boundary

Build the capture, storage, retrieval, and model-assisted search core independently
of both the cleanup tool and browser UI. A source adapter supplies bookmark
metadata through a small ingestion contract: source/profile identity, stable item
ID, original URL, title, folder path, saved date when known, and active membership.
Optional notes belong to the agent and do not depend on old review decisions.

The core accepts adapter records and complete snapshots; it does not read browser
databases or know about cleanup decisions. Unit tests use synthetic records and
captured-text fixtures. A minimal read-only browser snapshot adapter supplies real
items for search evaluation before full live synchronization is implemented.

The agentic part is bounded query interpretation, evidence selection, candidate
assessment, and search expansion. Collection membership is deterministic user
intent, not an autonomous model decision. Browser integration is replaceable;
the search core can be developed and tested without an installed extension.

## Product Decisions

1. Save using ordinary browser bookmarks inside Reads, including its subfolders.
2. Do not search browser history, normal bookmarks, or removed bookmarks.
3. Do not require a second save action, tags, summaries, or an LLM approval step.
4. Internal/public is a privacy property, not a relevance classification.
5. Search original page text, headings, titles, URLs, and user notes. Generated
   summaries are not substitutes for captured content or supporting evidence.
6. Never hide or delete a reading solely because it is old or hard to capture.
7. The first interface is a CLI. Add Control Center integration after search works.

Non-goals: autonomous bookmark cleanup, automatic recommendations, general web
search, browsing surveillance, cross-browser sync, and a new standalone dashboard.

## User Workflows

### Bootstrap

Connect the browser source, select the live Reads folder, and preview its current
items before accepting the first complete metadata snapshot. Preserve titles,
URLs, folder paths, and available saved dates. Applying the same snapshot twice
must not duplicate entries or discard capture progress.

Development uses the same ingestion contract with synthetic records and local
text fixtures. A future optional import adapter may accept a fresh bookmark export,
but exported files are not required for normal operation or core development.

Title/URL search works immediately. Content extraction and optional embeddings
are separate retryable jobs; their failure must not lose the saved reading.

### Save And Sync

Start with a minimal Edge extension adapter that reads a selected Reads subtree
through the bookmarks API for bootstrap and real-data evaluation. After the search
prototype passes evaluation, extend it with durable live synchronization. Creating,
editing, moving, and deleting bookmarks changes membership. Saving remains native.

Initial synchronization is metadata-only. Optional capture of the current rendered page
uses an explicit user action and `activeTab`/scripting permissions; unattended
capture on every site is not the default. Do not request history or broad page
access just to observe bookmarks.

### Search

Example proposed commands, not existing functionality:

```text
agb reads sources
agb reads sync --dry-run
agb reads sync
agb reads capture --pending
agb reads status
agb reads search "that explanation of latency numbers"
agb reads search "realtime session creation" --local-only
agb reads evaluate <private-evaluation-file>
```

Return a small number of strong matches, not a compulsory ten. Each result has
the original title, URL, a real matching excerpt, and a short explanation grounded
in that excerpt. Clearly distinguish content matches from title-only candidates.
No evidence means uncertainty or no match, not an invented answer.

## Architecture

```text
Synthetic test adapter ------------------------+
                                               v
Edge Reads adapter -> ingestion contract -> SQLite collection
                                                        |
                                      retryable capture / extraction
                                                        |
                                  versioned content + heading-aware passages
                                                        |
Query -> lexical search + evidence selection -> model assessment -> results
                                  ^
                     optional semantic retrieval when justified
```

Use the existing Python package, Click, settings conventions, and suitable shared
clients. Keep new modules under `agb/src/ab/agents/reads/`, with focused tests under
`agb/tests/`. Add modules only as the implementation needs them.

Use a separate database, proposed `~/.agb/reads/reads.db`. Do not migrate the
1,811 auto-selected FindTab entries into the new collection. Reuse infrastructure,
not the old classifier, watermark logic, or generated summaries.

### Stored Data

- Sources and memberships: adapter identity and browser installation/profile ID,
  bookmark ID, selected folder ID, original URL, title, folder path, saved date,
  user note, active membership, last complete sync revision.
- Documents: internal ID, original and resolved URLs, capture status, content
  hash, extractor version, fetched time, and privacy/cloud-processing policy.
- Content versions and passages: extracted text, heading path, stable passage ID,
  text offsets, verified publication/modified dates when available.
- Jobs: pending/running/succeeded/failed, attempt count, next retry, and last error.
- Search diagnostics: candidate and passage IDs, retrieval method, model/provider
  version, timings, coverage limitations, and errors; no full-content logs by default.

Multiple bookmark memberships may reference one document. Removing one membership
must not remove an item still present elsewhere in the selected subtree. Keep exact
URLs; conservative normalized keys only suggest duplicates. Do not drop identity
parameters, anchors, or authenticated document identifiers indiscriminately.

## Capture And Privacy

- Start with public HTML and established article extraction, initially evaluate
  Trafilatura. Support reference documentation and repository README content, not
  just prose articles. Validate extraction against the current selected collection.
- Add PDF extraction only when a selected reading requires it. Mark unsupported
  formats explicitly rather than treating empty extraction as success.
- Capture states include metadata-only, queued, captured, login-required,
  unsupported, unavailable, and failed. Status exposes coverage and last errors.
- Use bounded requests, redirects, response sizes, and retries. Validate every
  redirect destination; block loopback, private-network, link-local, and cloud
  metadata destinations in the public fetcher. Never forward browser cookies.
- Authenticated/internal material is local-only by default, including its title,
  URL, notes, excerpts, and embeddings. Public material also requires explicit
  opt-in before external model processing. A local-only override always wins.
- Do not identify sensitive content only by known corporate hostnames. Preserve
  per-item overrides and require explicit approval for uncertain destinations.
- Extension messages are narrowly scoped to collection sync and authorized
  capture. No arbitrary URL-fetch or command-execution endpoint.
- An unavailable page keeps its last successful content version with an age
  warning. Partial capture must be visible, not silently presented as complete.
- Treat page text as untrusted data. Models get no tools or authority from it.

## Accuracy-First Search

### Small-Collection Strategy

For a small collection, assess all eligible documents rather than trust an arbitrary
top-k cutoff. First implement a deterministic SQLite FTS5 baseline across titles,
URLs, notes, headings, and content. Exact technical identifiers get dedicated tests.

The model-assisted path builds query-specific evidence packs for every eligible
document. Long pages are split by heading with bounded overlapping passages.
Inspect passages in batches; preserve source IDs and track which content was
actually assessed. Do not silently truncate a page and claim it was ruled out.

Use a strong configured model to judge candidates against the user's recollection,
including negative constraints such as "not the Azure one." Ask for structured
assessments with document and passage IDs, evidence, and match strength. Validate
returned IDs and quotes against stored text before displaying them.

If evidence is insufficient, allow one bounded expansion over unassessed passages
or query variants. Default starting budget: 12 model calls and 120 seconds per
query, configurable and subject to measured cost. Reaching a limit produces an
explicit partial-search result, not a confident no-match.

Generative models must not invent numerical confidence probabilities. Decision-model
probabilities and confidence are provider estimates, not proven calibration
for this collection. Result categories such as strong, possible, or metadata-only
describe evidence quality. Ask a useful clarifying question when competing results
cannot be separated.

### Decision-Model Assessment Experiment

Use Azure's [Microsoft-Decision-1](https://ai.azure.com/catalog/models/Microsoft-Decision-1)
as the first specialized assessor, since the user reports access. Its model card
explicitly supports search/document relevance, rubric-based questions, and
groundedness assessment. Given supplied text and fixed answer options, it returns
a probability for each option rather than generated text. It is still model-based
assessment, not a deterministic rules engine or a replacement for retrieval.

Keep an assessor boundary with selectable structured LLM and Microsoft-Decision-1
implementations. An OpenAI Decisions adapter is an optional later comparison,
not a prerequisite. All consume the same query, constraints, document IDs, passage
IDs, and approved evidence packs. Keep retrieval, capture, membership, and privacy
policy independent of the assessment provider.

Start with these independent questions for each query/document evidence pack:

- Relevance: unrelated, topic overlap only, useful partial match, directly supported
  match to the requested reading, or insufficient evidence.
- Constraint violation: yes, no, or cannot tell, for an explicit user constraint.
- Evidence sufficiency: yes, no, or cannot tell, for judging the requested
  match; absence of a match in partial evidence is not proof about the whole page.

Select a supporting passage in a separate fixed-option question using supplied
passage IDs, with an explicit `none` option. Run dependent questions after their
prerequisite answers. For the initial experiment, favor simple per-document
requests over complex batching. Include all such calls in the shared query budget.

Microsoft-Decision-1 is text-only, has a 32K-token context window, and is currently
listed as preview. It does not generate explanations or rationales. Budget the
whole request, including questions and options, within the deployed model's limit;
split long documents into evidence packs and track unassessed passages. Abstention
must remain distinct from an unrelated judgment and must not silently exclude a
document whose evidence is incomplete.

Retrieve selected excerpts directly from local passage storage. Optional written
explanations use a separate structured LLM step and must cite validated evidence;
they are not required for decision-model results. Never reinterpret a relevance
score as a verified quote or factual check.

Record question/rubric versions, model and deployment identity, raw answer
distributions, provider-reported confidence and usage where available, latency,
cost, and content versions. Retain each provider's native response for evaluation;
do not assume scores from different providers are directly comparable. Fit
thresholds on labeled development queries, then measure on held-out queries.
Despite the model card's calibration claim, verify calibration on this collection;
do not treat probabilities as guarantees or multiply separate question
probabilities as if independent.

Compare lexical-only, structured LLM, and Microsoft-Decision-1 using identical
captured content and evaluation cases. Measure top-three retrieval quality,
no-match behavior, constraint handling, evidence selection, latency, and cost.
Inspect disagreements to learn where rubric design or missing evidence matters.
Do not assume the specialized model must outperform the LLM baseline.

For an optional OpenAI comparison, its
[Decisions API](https://developers.openai.com/api/docs/guides/decisions) exposes
`predicate`, `choice`, and `score` through `POST /v1/decisions`. Map the shared
rubric into provider-supported question formats with explicit sufficiency and
abstention handling. Its ordered-level score is a probability-weighted average
of level indices, not a percentage probability of finding the right article.
Do not assume Microsoft-Decision-1 accepts the same endpoint or request schema.

Before implementation, confirm the exact Microsoft-Decision-1 deployment, supported
inference endpoint, request/response schema, authentication, SDK support, and
current pricing from its deployment documentation or generated sample request.
User-reported access is not a verified inference test. Verify OpenAI access
separately only if that optional adapter is pursued. Start with synthetic/public
approved fixtures; credentials stay outside tracked files.
Handle refusals, missing/unknown answers, rate limits, and unavailable access as
visible assessment failures. Fallback must be explicitly labeled, and evaluation
must not silently substitute a different assessor.

Documentation was consulted while planning; no account access or real inference
request has been tested. This experiment does not enable cloud processing or
authorize sending private browser content to Azure, OpenAI, or another provider.

### Growth Strategy

Add local passage embeddings and lexical/semantic rank fusion when evaluation
shows paraphrase misses, or exhaustive assessment exceeds the agreed budget.
Start semantic experiments with an established local embedding model; pin the
model/version and rebuild embeddings when it changes.

At larger collection sizes, measure whether the intended document enters the
candidate set separately from its final rank. Expensive reranking cannot recover
an omitted candidate. Choose shortlist size from measured recall, not convention.

### Failure Behavior

Model unavailable: return lexical results and excerpts, labeled as lexical-only.
No embeddings: retain lexical search and bounded all-document assessment.
Missing content: return a clearly labeled metadata candidate where justified.
Bad structured model output: validate, retry within budget, then degrade visibly.
Never report a failed capture, sync, or model assessment as successful completion.

## Freshness Policy

Track bookmark save date, page publication/modified date, and capture date as
different facts. Missing dates remain unknown; fetch time is not publication time.

Freshness is contextual: event announcements and roadmaps age differently from
foundational explanations. Version-specific tutorials need applicability review;
maintained documentation may remain useful despite an old bookmark save date.

Show verified dates and cautious freshness warnings. Do not assert a page is
obsolete without supporting evidence or automatically remove it. Query terms such
as "current" or a specific version should influence assessment; age alone must not
override a strong content match. Refresh content explicitly or with a configurable
policy, preserving the last good capture on failure.

## Browser Integration And Reliability

Prefer extension-to-local-host native messaging to avoid exposing a general local
HTTP listener. Confirm packaging and OS permissions with a small Edge spike before
committing to the transport. If integration instead requires loopback HTTP, bind
only to loopback, authenticate requests, validate origin/sender, restrict extension
origins, and reject unauthenticated or replayed mutations. Never embed a shared
secret in the extension source.

Extension events need durable retry/acknowledgment and deduplication. Reconcile with
a complete subtree snapshot on startup/reconnect. Only a successfully completed
snapshot can establish absence; a failed or partial sync never removes membership.
Prevent overlapping capture of the same document and use transactional job state.

Moving out of Reads excludes the membership from search; it does not delete browser
bookmarks. Retain recoverable local content for a configurable period and provide
an explicit purge operation. Moving into Reads restores or creates membership.

## Evaluation And Release Gates

Before tuning retrieval, agree on a private evaluation file with the user:

- 20 answerable queries across the current live collection, including paraphrases, exact
  identifiers, vague recollections, version constraints, and overlapping subjects.
- At least 6 additional no-match or ambiguous queries, including normal bookmarks
  and out-of-collection items that must not appear as collection members. Use
  synthetic exclusion cases; deleted cleanup records are not required.
- Intended document IDs, acceptable alternatives, and evidence passages. Do not
  fabricate ground truth from generated summaries.

Proposed quality gate: intended item in the top three for at least 18/20 answerable
queries, with every failure inspected. All displayed supporting quotes must match
stored text. No fabricated high-confidence answer on the no-match cases. These
targets require user agreement and are not achieved results.

Report capture coverage, lexical baseline, model-assisted ranking, candidate recall,
evidence validity, latency, and provider cost separately. Keep evaluation data local
and outside tracked fixtures when it contains private bookmark metadata.

Required reliability checks: repeated snapshot ingestion, original URL preservation, failed
capture retry, last-good-content retention, job interruption recovery, privacy
enforcement for every provider, invalid model IDs/quotes, blocked fetch destinations,
duplicate memberships, partial sync, deletion/move reconciliation, and offline use.

## Delivery Plan

### Phase 1: Collection And Capture

- [ ] Register `agb reads` alongside the remaining Text and Shell commands.
- [ ] Define the ingestion contract and implement a synthetic source for core tests.
- [ ] Implement separate storage, capture states, retryable jobs, and status output.
- [ ] Prototype a minimal read-only Edge adapter for selecting Reads and previewing
  a complete snapshot, without depending on any cleanup artifact.
- [ ] Extract accessible public readings with source provenance and heading passages.
- [ ] Verify memberships against the accepted live snapshot and report captured vs
  metadata-only coverage. Do not require a particular collection count.

Exit: snapshot ingestion never loses entries, failures are visible, and captured content is
good enough to support real excerpts. Do not proceed on a misleading green status.

### Phase 2: Search Quality Prototype

- [ ] Establish user-confirmed evaluation queries before prompt/ranking tuning.
- [ ] Test the search core independently using synthetic records and captured-text
  fixtures; use the live snapshot for user acceptance, not old cleanup files.
- [ ] Implement lexical search and evidence excerpts as the offline baseline.
- [ ] Add privacy-controlled all-document model assessment and bounded expansion.
- [ ] Add a selectable Microsoft-Decision-1 assessor and versioned relevance rubric,
  including abstention; verify deployment/schema and inference with synthetic
  inputs before any approved real-content test.
- [ ] Validate evidence and add explicit no-match, ambiguity, and partial coverage.
- [ ] Compare lexical-only, structured LLM, and Microsoft-Decision-1 on shared cases;
  inspect disagreements, test thresholds, and select the default by measured accuracy.
- [ ] Optionally add OpenAI Decisions through a separate adapter for the same
  comparison; its availability must not block the Microsoft experiment.
- [ ] Run the evaluation, inspect misses, and add embeddings only where justified.

Exit: agreed quality gates pass; cost and latency are recorded and acceptable.
No new dashboard or automatic classification is required for this milestone.

### Phase 3: Native Bookmark Workflow

- [ ] Harden the prototype Edge transport and installation with least privileges.
- [ ] Select the live Reads folder by ID and reconcile its complete subtree.
- [ ] Implement create/edit/move/remove sync with durable retry and acknowledgments.
- [ ] Add optional user-triggered rendered-page capture for login/dynamic pages.
- [ ] Verify browser restart, disconnected host, missed events, and privacy defaults.

Exit: bookmarking into Reads reliably adds a searchable membership without manual
exports, browser database access, or dependence on Full Disk Access.

### Phase 4: Integration And Deployment

- [ ] Surface search, excerpts, capture coverage, and failures in Control Center.
- [ ] Confirm which checkout/package the running service loads before deployment.
- [ ] Install and restart the intended service; verify an end-to-end save and search.
- [ ] Get user acceptance on real queries before switching the primary search entry.
- [ ] Inspect the separate installation for legacy indexing jobs and disable them
  explicitly as part of the approved deployment, not repository cleanup.
- [ ] Retain historical data; delete it only with explicit approval.

The live Control Center currently uses a separate installation under
`~/.local/share/agent-box/control-center/`, not necessarily this working checkout.
Repository edits alone are not a deployment. Keep implementation and runtime
verification distinct, and do not modify that separate installation implicitly.

## Decisions To Confirm Before Their Phase

- Final command/product name; `reads` is a working name.
- Which local embedding/model provider and which strong cloud model are available.
- Exact Microsoft-Decision-1 deployment, inference schema/authentication, and
  approved experiment budget; access is reported but not yet tested.
- Whether approved content may go to Azure, and acceptable per-query cost.
- OpenAI Decisions access and separate content approval only if that optional
  comparison is pursued.
- User-confirmed evaluation queries and the acceptable search budget.
- Selected live Edge profile/folder and rendered-page capture permissions.

These do not block drafting this plan. Cloud processing and sensitive capture
remain disabled until explicitly approved.