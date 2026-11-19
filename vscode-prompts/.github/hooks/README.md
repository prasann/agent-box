# Personal Copilot hooks

These hooks are optional automatic actions. Review the JSON definitions and
[scripts](scripts/) before enabling them.

## What runs

| Definition | Events | Action |
| --- | --- | --- |
| [session-notifications.json](session-notifications.json) | `Stop` | Send a macOS completion notification with the repository name |

Definitions use version 1 and Copilot's compatible PascalCase event aliases,
which deliver snake_case fields to the existing scripts. Don't change event
names to camelCase without also adapting and testing the input payloads.

## Install

From the repository root:

```bash
./install-copilot.sh --with-hooks --dry-run
./install-copilot.sh --with-hooks
./install-copilot.sh --with-hooks --check
```

This creates native `~/.copilot/hooks` discovery and the
`~/.agent-box-toolkit/hooks` link used by the commands. `COPILOT_HOME` overrides
the native Copilot root if set. The compatibility link stays under your home
directory.

The old `./install-hooks.sh` command delegates to the same installer. Conflicts
are never deleted; use `--backup` to preserve and replace them.

Modern Copilot sessions in VS Code and CLI discover the native user hooks.
Remove the old `~/.agent-box-toolkit/hooks` entry from the VS Code
`chat.hookFilesLocations` setting to avoid loading the same hooks twice. Legacy
Local sessions may still need that setting. Start a fresh session after setup.

## Dependencies and behavior

- Notifications require macOS. Install `terminal-notifier` with
  `brew install terminal-notifier` for grouped, clickable notifications.
  The script falls back to `osascript` if it isn't installed.
- Notification clicks focus VS Code Insiders when installed, otherwise Stable.
- Notification logs go to `~/.agent-box/logs/notifications.log`.

The old custom branch-attribution hook and script have been removed. Notification
installation no longer enables telemetry or depends on a collector. Existing
attribution logs and opt-out markers are left untouched. See the
[telemetry revival plan](../../TELEMETRY_PLAN.md) for a separate, opt-in replacement.

Dependencies and user paths must exist on the host where the agent runs.
Installing links on your laptop doesn't configure remote hosts or containers.

## Verify

Send a synthetic completion event on macOS:

```bash
printf '%s\n' '{"hook_event_name":"Stop","cwd":"/tmp/example-project"}' |
  bash ~/.agent-box-toolkit/hooks/scripts/notify.sh
```

Then start a fresh Copilot session in another repository and confirm the hooks
appear in **Chat: Open Customizations**, under **Hooks**. Finish a turn and
check the notification and log. A direct script test doesn't prove runtime
discovery.

For persistent alerts, set the notification style to **Alert** in macOS
notification settings. If notifications don't appear, check notification
permissions and the agent's hook debug output. If the script reports
`Notifications are not allowed for this application`, enable notifications for
`terminal-notifier` in **System Settings > Notifications**, then repeat the test.
Creating symlinks does not grant macOS notification permission.

User and repository hooks run together; repository hooks don't override these
user hooks. See the official [VS Code hooks guide](https://code.visualstudio.com/docs/agent-customization/hooks)
and [Copilot hooks reference](https://docs.github.com/en/copilot/reference/hooks-reference).
