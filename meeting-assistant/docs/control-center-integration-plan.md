# Control Center Integration Plan

## Decision

Integrate Meeting Assistant as a first-class agent in the existing Agent Box
Control Center. The Control Center becomes the only normal browser UI:

```text
agb serve
  └── http://127.0.0.1:4747
      ├── Dashboard
      ├── Text
      ├── FindTab
      ├── Meeting
      ├── Library
      └── Shell
```

This is feasible with the current architecture. The important boundary is not
where every file lives; it is which layer owns which responsibility:

- `meeting-assistant/` continues to own capture, transcription, persistence,
  suggestion scheduling, provider adapters, meeting state, and audit behavior.
- `web-app/backend/` adapts those capabilities into the Control Center process.
- `web-app/frontend/` owns the single React presentation.
- `agb` remains the package and CLI composition root.

The standalone meeting HTML UI should be retired after the integrated view
reaches feature parity. Keeping two production UIs would create duplicate state,
security, lifecycle, and accessibility work.

## User Experience

### Primary path

1. Run `agb serve` or use the existing always-on Control Center setup.
2. Select **Meeting** in the left navigation or dashboard.
3. Select Teams output and microphone devices.
4. Start and stop recording in the same Control Center window.
5. Watch the live `Me` and `Meeting` transcript, manage suggestions, and browse
   prior meetings without opening another local application.

The Meeting navigation item shows a recording indicator while capture is active.
Leaving the Meeting view must not stop recording; the persistent app shell keeps
the status visible and allows returning to the session.

### CLI compatibility

The existing commands remain useful, but target the unified application:

- `agb meeting start`: start the Control Center in the foreground at the Meeting
  route when it is not running; otherwise open/focus the Meeting route.
- `agb meeting open`: open `http://127.0.0.1:4747/#/meeting`.
- `agb meeting status`: query the unified Meeting API and print recording,
  devices, segment count, suggestion status, and any errors.
- `agb serve`: start the same process with the Dashboard route as the default.

There must never be two independently recording `MeetingManager` instances.
Port `8765` and the standalone meeting server are removed from the normal path
after migration.

## Target Architecture

```text
Control Center React SPA
  ├── existing agent views
  └── MeetingView
       ├── REST: setup, history, actions
       └── WebSocket: status, transcript, suggestions, errors
                 │
                 ▼
Control Center FastAPI process (`agb serve`)
  ├── existing routes
  └── meeting router / lifecycle adapter
                 │
                 ▼
isolated `meeting-assistant` package
  ├── MeetingManager
  ├── SoundDeviceCapture
  ├── MlxWhisperTranscriber
  ├── MeetingStore
  ├── SuggestionCoordinator
  └── Agent Box provider adapters
```

### Process ownership

Create exactly one `MeetingManager` during Control Center FastAPI lifespan and
store it on `app.state`. Shutdown must stop an active capture session, flush STT
tails, finalize metadata/Markdown, and close scheduler resources using the
existing bounded shutdown behavior.

The manager must not be constructed while importing the backend. This preserves:

- transcript-only startup without probing Ollama, Azure, audio devices, or MLX;
- test injection of fake capture/transcription/providers;
- reload safety; and
- one manager per server process.

### Backend boundary

Add `web-app/backend/meeting.py` as the Control Center adapter. It should not
reimplement meeting domain logic. It will:

- own the FastAPI router and request/response models;
- obtain the manager from app state;
- expose device, session, suggestion, and history operations;
- translate known domain errors to actionable HTTP responses;
- bridge manager events to authenticated WebSocket subscribers; and
- expose a small health summary for the agent registry.

Refactor reusable event subscription and scheduling primitives out of
`meeting_assistant.api` into package-level transport-neutral services where
needed. Both capture and persistence remain unaware of FastAPI.

Planned routes:

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api/meeting/status` | Recording, counts, settings, errors |
| `GET` | `/api/meeting/config` | Safe defaults and provider model choices |
| `GET` | `/api/meeting/devices` | Available input devices |
| `POST` | `/api/meeting/session` | Start a session |
| `DELETE` | `/api/meeting/session` | Stop and finalize a session |
| `PATCH` | `/api/meeting/session/suggestions` | Enable/disable/change cadence |
| `POST` | `/api/meeting/session/suggestions` | Generate now |
| `PATCH` | `/api/meeting/suggestions/{id}` | Edit/copy/dismiss/mark-used audit |
| `GET` | `/api/meeting/history` | Scan prior meeting directories |
| `GET` | `/api/meeting/history/{directory}` | Transcript and audit detail |
| `WS` | `/api/meeting/events` | Live status, segments, suggestions, errors |

Copy remains a browser operation, but the corresponding audit action is sent to
the API after a successful clipboard write.

### Security

Meeting endpoints cannot inherit the current assumption that localhost alone is
authentication. Cross-origin websites and local processes must not be able to
read transcripts or control recording.

Unify the existing Meeting Assistant launch-token protection with Control
Center:

1. `agb serve` creates a random token in a user-only `0600` runtime file.
2. The same-origin React application receives the token through a bootstrap
   mechanism that does not put it in access logs.
3. Meeting REST requests send it in a private header.
4. The Meeting WebSocket authenticates without placing the token in the URL,
   preferably with a negotiated WebSocket subprotocol.
5. Backend middleware validates loopback Host and same-origin Origin.
6. Access logs redact or omit all credentials.

The implementation should either protect the whole Control Center consistently
or narrowly protect all Meeting routes plus their bootstrap. The first option is
preferred because FindTab history and library contents are also private local
data.

### Frontend boundary

Add a dedicated `MeetingView` component rather than extending the already-large
`App.tsx` with all meeting behavior. Suggested layout:

```text
web-app/frontend/src/features/meeting/
├── MeetingView.tsx
├── MeetingSetup.tsx
├── LiveTranscript.tsx
├── SuggestionPanel.tsx
├── MeetingHistory.tsx
├── useMeetingEvents.ts
├── meetingApi.ts
└── meetingTypes.ts
```

Use the existing React, TanStack Query, Lucide, Tailwind, and component library.
Do not add another frontend toolchain or embed the old page in an iframe.

The view must preserve current functionality:

- separate Teams and microphone device selection;
- visible `Meeting` and `Me` provenance;
- start/stop and persistent recording status;
- transcript-only mode;
- provider/model selection and Azure egress warning;
- suggestion toggle, cadence, and Generate now;
- editable suggestion cards with copy/dismiss/mark-used;
- visible capture/provider errors; and
- prior meeting transcript/audit browsing.

Use REST for commands and initial snapshots. Use one reconnecting WebSocket for
live events. On reconnect, invalidate the status and active-session queries so
missed events are recovered from canonical server state rather than assumed.

### Agent registry

Register a `meeting` manifest in `web-app/backend/registry.py` with a microphone
icon, health state, and actions describing Start, Stop, and Generate now.

Update `/api/agents` health assembly so Meeting reports:

- `healthy`: package and audio dependencies load and input devices can be listed;
- `recording`: active meeting, represented separately from dependency health;
- `unavailable`: optional `ab[meeting]` dependencies are absent;
- `degraded`: last capture/STT/provider error exists, while transcript-only
  operation may still be available.

The dashboard tile and sidebar show a red recording dot independently of health.
The command palette includes Meeting automatically through the registry.

## Package and Installation Strategy

Keep `meeting-assistant` as an isolated top-level package. Control Center imports
its public interfaces through the existing optional Agent Box extra:

```bash
uv sync --project agb --extra meeting
```

Plain pip and pipx continue using the documented two-package install/injection.
When the optional package is absent:

- `agb serve` and every existing agent still work;
- the Meeting tile is visible but unavailable;
- the UI displays the exact install command; and
- backend imports fail lazily, not at Control Center startup.

This preserves isolation without forcing MLX, NumPy, SoundDevice, and model
dependencies onto users who only use other Agent Box agents.

## Migration Plan

### Phase 1: Backend composition

1. Extract transport-neutral meeting event subscription/scheduler wiring from
   the standalone API without changing capture or persistence behavior.
2. Add the Control Center meeting router and inject one manager during FastAPI
   lifespan.
3. Add Meeting registry metadata and health reporting with lazy optional imports.
4. Protect Meeting APIs and WebSocket with the unified token/origin policy.
5. Point CLI status/open behavior at the Control Center API and Meeting route.

Exit criteria:

- existing meeting domain tests remain green;
- API tests cover lifecycle, live events, auth, optional dependency errors, and
  shutdown with blocked provider work;
- only one manager can own audio capture in a process.

### Phase 2: Integrated React view

1. Add Meeting to the view type, navigation, icon map, dashboard, and palette.
2. Implement setup and active-recording state with React Query.
3. Implement the reconnecting event hook and live transcript.
4. Implement suggestions and all audited card actions.
5. Implement history and prior-meeting detail.
6. Add a shell-level recording indicator that remains visible on every view.

Exit criteria:

- feature parity with the standalone browser UI;
- keyboard navigation and responsive layouts work;
- disconnect/reconnect does not duplicate transcript or suggestion items;
- navigating away never stops capture; and
- the production frontend build is served by `agb serve`.

### Phase 3: Single-UI cutover

1. Make `agb meeting start/open/status` target the unified Control Center.
2. Remove the standalone static HTML and normal standalone server entry point.
3. Keep a package-level diagnostic command only if it provides unique hardware
   troubleshooting value; it must not be a second general UI.
4. Update setup, privacy, BlackHole, and operation documentation around
   `agb serve`.
5. Remove obsolete port/token runtime files and compatibility code after testing.

Exit criteria:

- the normal workflow has one URL, one server process, and one UI;
- no duplicated frontend implementation remains;
- active sessions finalize safely when Control Center exits; and
- fresh uv, pip editable, and pipx installs follow tested documentation.

## Test Plan

### Backend and domain

- Control Center starts when the Meeting extra is absent.
- Exactly one manager is created and stopped through app lifespan.
- Device/start/stop/config/suggestion/history routes delegate to the package.
- Transcript-only start constructs no provider and makes zero LLM calls.
- Capture/STT/provider failures remain visible without losing persisted segments.
- WebSocket sends initial status, live provenance segments, suggestions, and
  errors; reconnect obtains a canonical snapshot.
- Invalid token, Host, Origin, and WebSocket authentication are rejected.
- Server shutdown remains bounded during blocked provider generation.
- Starting a second capture is rejected deterministically.

### Frontend

- Meeting appears in navigation, dashboard, and command palette.
- Setup requires separate devices and enforces provider selection only when
  suggestions are enabled.
- Azure selection shows the egress warning and never inherits an Ollama model.
- Live event reduction is idempotent by segment/suggestion ID.
- Start/stop, cadence, Generate now, edit, copy audit, dismiss, and mark-used
  send the expected requests.
- Recording indicator persists while another agent view is active.
- History renders transcript-only and suggestion-audited meetings.
- WebSocket reconnect invalidates and reloads active state.

### Build and end-to-end

- Python meeting and Agent Box test suites.
- Backend route tests with fake capture/STT/providers.
- Frontend TypeScript build and existing lint.
- Production asset build into `web-app/backend/static`.
- `agb serve` on loopback with real audio-device enumeration.
- Start a fake meeting through the React UI, stream both provenances, generate a
  fake suggestion, stop, and reopen it from history.
- Manual hardware smoke test using Teams, BlackHole/Multi-Output, headphones, and
  microphone after explicit participant consent.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Control Center reload creates two audio owners | Lifespan-owned singleton, explicit stop, and reload warning while recording |
| Optional ML dependencies break existing agents | Lazy import plus `ab[meeting]` extra and unavailable tile state |
| WebSocket misses events | Canonical snapshot on connect/reconnect; IDs make reductions idempotent |
| Browser navigation stops meeting | Manager belongs to backend process, not React component lifecycle |
| Provider call delays shutdown | Retain bounded daemon worker and discard post-stop results |
| Two UIs drift | Remove standalone production UI only after integrated feature parity |
| Local website attacks read transcripts | Random token, loopback Host validation, Origin validation, no token in URLs/logs |
| Frontend monolith becomes harder to maintain | Feature folder and typed API/event reducer rather than adding logic to `App.tsx` |

## Definition of Done

- `agb serve` is the single normal UI for all Agent Box agents, including Meeting.
- Meeting is visible in navigation, dashboard, health, and command palette.
- All current recording, transcript, suggestion, audit, and history behavior is
  available in the integrated view.
- `agb meeting` commands route to the unified process and do not launch a second
  server.
- The standalone meeting frontend is removed after parity.
- Optional dependency absence does not affect other agents.
- Security, domain, API, frontend, build, and fake end-to-end tests pass.
- A consented hardware smoke test verifies separate `Me` and `Meeting` capture on
  the target Mac.
