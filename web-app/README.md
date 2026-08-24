# Prasanna's Control Center

All Control Center code lives in this folder, alongside the repository's `xbar/` integration.

```text
web-app/
├── backend/   # FastAPI API, registry, jobs, library reader, built frontend
└── frontend/  # React, Vite, and TypeScript source
```

The backend imports agent implementations from `agb/src/ab/`; it does not duplicate agent logic.
The `agb serve` command is a small launcher bridge that loads this folder from an editable checkout.

## Build

```bash
cd web-app/frontend
pnpm install
pnpm build
```

The production build is written to `web-app/backend/static/`.

## Run

```bash
cd agb
uv sync
uv run agb serve
```

Agent configuration is shared with xbar and other checkouts through
`~/.agb/.env`. To initialize it from the example:

```bash
mkdir -p ~/.agb
cp agb/.env.example ~/.agb/.env
```
