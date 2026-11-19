# Personal Copilot toolkit

This repository is the source of truth for personal skills, agents, prompts,
templates, and hooks. Clone it anywhere on each machine, then link it into
Copilot's native user folders. No multi-root workspace or copied skills needed.

## Install

From the repository root:

```bash
./install-copilot.sh --dry-run
./install-copilot.sh
./install-copilot.sh --check
```

The installer creates these directory symlinks:

| User location | Repository source |
| --- | --- |
| `~/.copilot/skills` | `vscode-prompts/.github/skills` |
| `~/.copilot/agents` | `vscode-prompts/.github/agents` |

These are native personal customization locations for the modern Copilot harness
in VS Code Stable, VS Code Insiders, and Copilot CLI. No editor settings file is
required. Start a fresh session after installing and use **Chat: Open
Customizations** to check discovery. The installed client must support these
locations; update older clients rather than relying on workspace mounting.

`COPILOT_HOME`, when set, replaces `~/.copilot` as the destination root. The path
must be absolute. Set it consistently in the clients where you want these
customizations. Run the installer from a real checkout, not a symlink to the
installer file.

### Safety and conflicts

- Correct links are left alone; running setup again is safe.
- All requested destinations are checked before any links are changed.
- A conflicting file, directory, or broken link stops setup.
- Use `./install-copilot.sh --backup` to move conflicts to timestamped sibling
  paths before replacing them. Backup locations are printed. Existing personal
  customizations are preserved there, but aren't automatically merged or loaded.
- `--dry-run` writes nothing; `--check` exits nonzero for missing or incorrect links.
- The installer does not edit editor settings, install dependencies, or touch
  credentials.

The script requires Bash and standard macOS/Linux utilities. It is not a native
Windows installer. For remote development, install on the host where Copilot runs.

## Optional hooks

Hooks execute commands automatically. Review [the hook documentation](.github/hooks/README.md)
and scripts before enabling them:

```bash
./install-copilot.sh --with-hooks --dry-run
./install-copilot.sh --with-hooks
./install-copilot.sh --with-hooks --check
```

This additionally links `~/.copilot/hooks` to `.github/hooks` in this toolkit
(under `vscode-prompts/`), and retains the `~/.agent-box-toolkit/hooks` compatibility
link used by the hook commands. Hooks provide macOS completion notifications;
they do not enable telemetry.

The old `./install-hooks.sh` command now delegates to this safe installer with
`--with-hooks`; it installs skills and agents too.

When using the modern Copilot harness, remove the old
`"~/.agent-box-toolkit/hooks": true` entry from `chat.hookFilesLocations` in each
editor profile to avoid duplicate hook sources. Native user hooks don't need that
setting. Legacy Local sessions may still require it; don't configure both sources
for the same harness.

## Telemetry

Telemetry is separate from skills, agents, and notifications. The unfinished
custom branch-attribution integration has been removed. On the machine where
this cleanup was performed, Copilot OTel export and content capture were
explicitly disabled in Insiders settings; the installer does not change those
settings on other machines.

The [telemetry revival plan](TELEMETRY_PLAN.md) describes a future local-only,
metadata-only Grafana OSS stack using Docker. No backend has been installed or
started. Existing telemetry data and the old-Mac snapshot are preserved.

## Layout

- [Skills](.github/skills/): reusable workflows and their scripts/resources.
- [Agents](.github/agents/): specialized roles for planning, implementation, and review.
- [Templates](.github/templates/): supporting resources, not independently installed.
- [Hooks](.github/hooks/): optional automatic actions.
- [Legacy prompts](.github/prompts/): retained for Local-harness compatibility.

The legacy `agb.pr-desc` and `agb.pull-story` prompts also have portable skill
equivalents: `agb-pr-desc` and `agb-pull-story`. Prefer the skills for new sessions.
The Azure DevOps workflow still needs a configured work-item integration; symlinks
do not install MCP servers or credentials.

## Why this layout?

Agent Skills are now an open standard. Copilot also supports `~/.agents/skills`,
which is useful when sharing skills with other compatible agents. This toolkit
uses only `~/.copilot/skills` for the selected Copilot clients, avoiding duplicate
discovery. Its source directory can stay inside the repository regardless of the
consumer's expected location.

Plugins and marketplaces are useful for distributing versioned bundles to others;
they add unnecessary packaging for this personal, live-checkout setup. There is no
need to move every skill or introduce a plugin just to share it across machines.

VS Code's current documentation limits `.prompt.md` execution to the deprecated
Local harness, scheduled for removal in February 2027. Skills are the portable
replacement. See the official [skills](https://code.visualstudio.com/docs/agent-customization/agent-skills),
[agents](https://code.visualstudio.com/docs/agents/reference/custom-agent-file-reference),
[prompts](https://code.visualstudio.com/docs/agent-customization/prompt-files), and
[hooks](https://code.visualstudio.com/docs/agent-customization/hooks) documentation.

## Updating, moving, and removing

Run `git pull` in this checkout to update all linked clients. Review hook changes
before updating because hooks execute automatically. Don't put secrets or generated
session state in this repository.

If you move the checkout, rerun setup with `--backup` to preserve and replace stale
links. To uninstall, inspect the links and remove only those created by the
installer with `unlink`; don't recursively delete their targets. Restore any
backups to their original locations if needed.

Installer tests: `bash tests/install-copilot.test.sh` from the repository root.
