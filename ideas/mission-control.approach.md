---
title: Mission Control - Local Web Control Center for Agent Box
description: Plan for a local, always-on web dashboard that runs, monitors, and documents every agent in this repo, with a showcase-quality UI.
author: Prasann Nagarajan
ms.date: 2026-08-24
ms.topic: overview
---

## Mission

Build a single, always-on web application that acts as the control center for every agent in Agent Box. Today the agents live behind a CLI and an xbar menu, and results land back in the terminal. Mission Control replaces that scattered experience with one browser home base where I can run agents, watch long-running jobs, read results as rich content, and browse the prompt and skill library that powers my VS Code workflows.

The application runs locally, starts automatically at login, and is reachable with a single click in the browser. Because it is personal and local-only, the design optimizes for my workflow first. The UI quality is high enough to demo to teams and use as a reference for how a personal agent hub can look.

## Constraints

* Runs entirely on my Mac; no remote hosting, no cloud deployment.
* Binds to `127.0.0.1` only, so no authentication layer and no network exposure.
* Reuses the existing agent classes (`BookmarkSearcher`, `GrammarChecker`, `SafePurger`) directly instead of shelling out to the CLI, keeping one source of truth for logic.
* Shares the existing configuration, virtual environment, and Azure or Ollama credentials already wired through `get_settings()`.
* Coexists with xbar during the transition; xbar keeps working and is not removed.
* Portability is a non-goal. This is tuned for one machine and one user.

## Must-Haves

* One command (`agb serve`) starts the whole application: API plus built frontend.
* Auto-start at login through a `launchd` LaunchAgent, kept alive across crashes and restarts.
* A dashboard home that lists every agent with live health and quick access to its actions.
* FindTab search available front and center, since that is the most frequent need. Results render as clickable cards that open the source tab in a new browser tab.
* A read-only library view that lists and reads the agents, prompts, skills, instructions, and hooks under the `vscode-prompts` folder. Editing still happens in VS Code.
* Global health indicators for Azure sign-in, Ollama reachability, and database presence.
* Top-class UI and UX built on a real framework and CSS system, themeable and demo-ready.

## Architecture

The system splits into a Python API and a modern single-page application. The split lets the backend keep owning agent logic while the frontend focuses on presentation and interaction quality.

```text
Browser (SPA)  ->  FastAPI (agb serve)  ->  Agent classes + config
   React            JSON APIs               BookmarkSearcher
   Tailwind         /api/agents             GrammarChecker
   shadcn/ui        /api/health             SafePurger
                    /api/library            Library reader
```

### Backend

The backend is FastAPI, added as a new agent group under `agb/src/ab/agents/web/` with an `app.py` and a `commands.py` that exposes `agb serve`. It registers alongside the existing groups in the main CLI entry point, so it ships with the same install.

Planned endpoints:

* `GET /api/agents` returns the registry manifests that drive the dashboard tiles and action forms.
* `GET /api/health` returns aggregate and per-agent status for the badges.
* `POST /api/agents/{id}/actions/{action}` invokes an agent action by calling the same classes the CLI uses.
* `GET /api/agents/{id}/runs/{run_id}` streams progress for long-running jobs such as FindTab indexing.
* `GET /api/library` walks the `vscode-prompts` folder, parses YAML frontmatter, and returns a grouped catalog plus raw markdown for the reader.

In production the FastAPI process also serves the built frontend assets, so a single process runs everything.

### Frontend

The frontend uses React with Vite and TypeScript, styled with Tailwind CSS and shadcn/ui components. This stack produces premium-looking dashboards, is fully themeable for a team demo, ships accessible components, and avoids heavy runtime lock-in. Mantine or Chakra UI are viable alternatives if I want a more batteries-included component set with less setup.

Supporting libraries:

* TanStack Query for data fetching and caching.
* `react-markdown` with remark and rehype plus Shiki for VS Code-quality syntax highlighting in the library reader.
* Frontmatter parsing handled on the backend so the frontend receives clean metadata.

During development, the Vite dev server proxies API calls to FastAPI. A production build emits static assets that `agb serve` mounts.

### Agent registry

Each agent describes itself through a small manifest: id, display name, icon, a health check, and a list of actions with input schema, a read-only or destructive flag, and a long-running flag. The dashboard renders itself from these manifests. Adding a future agent, such as Gmail or Calendar, means registering a manifest and the control center picks it up with no dashboard rewrite. This mirrors how the CLI already registers command groups.

## Features

### Dashboard home

A grid of agent tiles shows name, icon, a one-line status, and last-run information. A prominent FindTab search box sits at the top for the most common task. A recent-activity strip lists recent runs and their outcomes so the app feels like a real control center.

### FindTab

Search is the primary path. Results render as cards with title, category icon, summary, topic chips, and last-visited time, and clicking a card opens the source URL in a new tab. Indexing runs as a background job with live progress through server-sent events, which replaces the notification model xbar uses today. A status view surfaces index size and health.

### Text

Fix and rewrite actions take text in a request body and return the improved text with a copy button. Browsers cannot read the system clipboard the way the xbar text agent does, so the web version uses paste-in and copy-out. This is the one behavior difference from xbar.

### Shell

The web UI exposes the history purge preview only. The destructive purge stays on the CLI to keep a clear safety boundary.

### Library

The library is a browsable, read-only catalog of everything under the `vscode-prompts` folder. It groups content by type: agents, prompts, skills, instructions, and hooks. Each item shows a card built from its frontmatter name and description. Selecting an item renders the markdown with syntax highlighting and a metadata header.

Extra touches that bridge viewing here and editing in VS Code:

* A command palette (Cmd+K) to jump to any agent, skill, or prompt.
* An Open in VS Code button per item using the `vscode://file/<absolute-path>` URI.
* Copy-to-clipboard for a skill path or name.

The library has no write endpoints, so it is safe to demo.

## Layout and UX

The application shell has a left navigation for Dashboard, FindTab, Text, Shell, Library, and future agents. A top bar carries the global health badges and the Cmd+K palette. Agent views render their action forms from the manifest and show results inline. Theming supports light and dark with a tuned color system and spacing. This is where the shadcn and Tailwind investment pays off for a team showcase.

## Access and Autostart

* `agb serve` starts uvicorn bound to `127.0.0.1` on a fixed port (for example 4747).
* A `launchd` LaunchAgent runs `agb serve` at login with KeepAlive, following the pattern already used by `install-xbar.sh`. A new `install-web.sh` writes the plist and loads it.
* Reaching the app is a single action: a browser bookmark, a Raycast or Spotlight shortcut that runs `open http://localhost:4747`, and one xbar item labeled Open Mission Control so the two tools coexist during the transition.

## Repository Layout

* `agb/src/ab/agents/web/` holds the FastAPI application and the `agb serve` command.
* A sibling `web/` folder holds the Vite React application.
* The package build copies or mounts the built frontend assets so `agb serve` can serve them.

## Dependencies

* Backend adds `fastapi` and `uvicorn` to `pyproject.toml`. `pyyaml` is already present for frontmatter parsing.
* Frontend introduces a Node and npm toolchain for the Vite build. This is more setup than static HTML, and it is the deliberate cost of showcase-quality UI. Everything still runs locally.

## Safety and Privacy

* The server binds to localhost only, so nothing is exposed on the network.
* Destructive actions stay off the web UI; the real shell purge remains CLI-only.
* The library is strictly read-only.

## Build Order

1. FastAPI skeleton with `/api/health` and `/api/agents`, plus a Vite, React, Tailwind, and shadcn scaffold with the app shell and dashboard.
2. FindTab search end to end, with polished result cards. This delivers the primary need first.
3. Library module: `/api/library`, the catalog and reader, and Open in VS Code. This is the piece to showcase.
4. `launchd` autostart, `install-web.sh`, and the open-in-browser shortcut.
5. FindTab index with streamed progress, then Text, then Shell preview, then future agents through manifests.
