# Meeting Assistant

A private, local macOS assistant for Microsoft Teams meetings. It captures Teams
output and the microphone as separate streams, labels finalized transcript
segments as `Meeting` or `Me`, and can optionally suggest useful questions in a
localhost browser UI. It never joins a meeting, posts to Teams, or saves raw audio
by default.

## Install

The supported repository install keeps `meeting-assistant` isolated while making
it available to the thin Agent Box command:

```bash
brew install portaudio
uv sync --project agb --extra meeting --extra dev
```

The `meeting` extra is resolved by uv to the sibling package through
`agb/pyproject.toml`. Agent Box supplies its existing optional Ollama/Azure
clients without creating a reverse dependency cycle.

Standard pip and pipx do not interpret uv's local-source table. Use one of these
repository-local installs instead:

```bash
# pip / editable development install
python3.13 -m venv .venv
.venv/bin/pip install -e './meeting-assistant[audio,stt]' -e ./agb

# pipx
pipx install ./agb
pipx inject ab './meeting-assistant[audio,stt]'
```

The base `ab` wheel remains independently pip-resolvable; its `meeting` extra is
only for uv repository installs. For tests and API browsing without physical
audio or a model download, only the meeting package's base and `dev` dependencies
are needed:

```bash
uv sync --project meeting-assistant --extra dev
```

The first real transcription downloads the configured MLX Whisper model. The
default, `mlx-community/whisper-small-mlx`, is a practical starting point for an
Apple M1 Pro with 32 GB RAM.

## Route Teams audio with BlackHole

1. Install BlackHole: `brew install blackhole-2ch`.
2. Open **Audio MIDI Setup**, click **+**, and create a **Multi-Output Device**.
3. Include both your normal speakers/headphones and **BlackHole 2ch**. Enable
   drift correction for BlackHole when it is not the clock source.
4. In Teams **Settings → Devices**, set **Speaker** to the Multi-Output Device.
5. In Meeting Assistant, select **BlackHole 2ch** for Teams output and your
   physical microphone for `Me`.
6. Grant microphone permission to the terminal/Python process when macOS asks.

Use headphones to prevent the microphone from recapturing meeting output.
BlackHole appears as an input to this app even though Teams sends output to it.

## Run

```bash
uv run --project agb --extra meeting agb meeting start
```

The command binds only to `127.0.0.1:8765`, opens the browser, logs lifecycle
events in the foreground, and stops on `Ctrl+C`.
Each launch creates a random access token in a user-only `server-<port>.json`
file. REST and WebSocket requests require that token, and browser connections
must have a matching loopback origin.

```bash
uv run --project agb --extra meeting agb meeting open
uv run --project agb --extra meeting agb meeting status
uv run --project agb --extra meeting agb meeting start --port 8877 --no-open
```

In the UI, select both devices before starting. You can record in transcript-only
mode, turn suggestions on or off, change the default five-minute cadence,
generate immediately, edit/copy/dismiss/mark-used cards, and browse prior
meeting transcripts and suggestion audits.

### Consent and privacy

Get the consent required by your organization and local law before recording or
transcribing anyone. Audio is processed in memory and is not persisted. Ollama
runs locally. Azure OpenAI is explicit opt-in and the UI warns that transcript
excerpts and compact meeting state leave the Mac for the configured Azure
deployment. The assistant never sends messages to Teams.

## Models and providers

### Transcript only

Leave **Suggestion provider** set to **Transcript only**. This mode constructs no
provider, makes zero LLM calls, and still writes metadata and transcripts.

### Ollama

```bash
brew install ollama
ollama serve
ollama pull qwen3:4b
```

`qwen3:4b` is the default suggestion model with low temperature and a
non-chain-of-thought JSON prompt. `qwen3:8b` and arbitrary installed model names
can be entered in the UI.

### Azure OpenAI

Azure is opt-in. Authenticate with `az login`, then configure Agent Box:

```bash
mkdir -p ~/.agb
cat >> ~/.agb/.env <<'EOF'
AB_AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE.openai.azure.com
AB_AZURE_OPENAI_DEPLOYMENT=gpt-4o
EOF
```

Provider failures are shown in the UI and audit trail without stopping local
transcription or persistence.

## Storage

Each meeting is a directory under:

```text
~/.local/share/meeting-assistant/meetings/<timestamp>-<session-id>/
├── metadata.json
├── transcript.jsonl
├── transcript.md
└── suggestions.jsonl   # only after a generation call
```

`metadata.json` is atomically replaced. `transcript.jsonl` is the canonical,
append-only transcript and every finalized segment is flushed and synced
immediately. `transcript.md` is rebuilt when recording stops.
`suggestions.jsonl` preserves each original structured response and later
edit/copy/dismiss/mark-used actions. No SQLite database is required.

Optional environment defaults:

| Variable | Default |
|---|---|
| `MEETING_ASSISTANT_PORT` | `8765` |
| `MEETING_ASSISTANT_DATA_DIR` | `~/.local/share/meeting-assistant` |
| `MEETING_ASSISTANT_STT_MODEL` | `mlx-community/whisper-small-mlx` |
| `MEETING_ASSISTANT_OLLAMA_MODEL` | `qwen3:4b` |
| `MEETING_ASSISTANT_OLLAMA_URL` | `http://localhost:11434` |
| `MEETING_ASSISTANT_SUGGESTION_INTERVAL_MINUTES` | `5` |

## Architecture

- `audio.py`: separate `sounddevice` streams, mono resampling, VAD/chunking
- `transcription.py`: replaceable STT protocol and MLX Whisper adapter
- `storage.py`: crash-conscious metadata and append-only audit files
- `suggestions.py`: incremental compact state, overlap, cadence, and deduplication
- `providers.py`: explicit adapters over Agent Box `OllamaClient` and
  `AzureOpenAIClient`
- `runtime.py`: orchestration that isolates provider failures from transcription
- `api.py` and `static/`: loopback FastAPI/WebSocket UI without a Node toolchain

Remote-speaker diarization and video are intentionally out of scope.

## Tests

Tests use fake capture, transcription, and providers, so they require no audio
device, model download, Ollama, or Azure:

```bash
uv run --project meeting-assistant --extra dev pytest
uv run --project meeting-assistant --extra dev ruff check
uv run --project agb --extra dev pytest agb/tests/test_meeting_command.py
```
