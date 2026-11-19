# Current prompts, skills, and hooks setup

This document records the configuration verified on the current Mac and how to
recreate it on another laptop.

## Repository location

```text
/Users/pnagarajan/projects/personal/agent-box/vscode-prompts
```

The shared configuration is stored under [`.github`](.github):

| Directory | Contents |
|---|---|
| [`agents`](.github/agents) | Custom agent definitions |
| [`skills`](.github/skills) | Reusable skills and their supporting files |
| [`prompts`](.github/prompts) | Reusable `.prompt.md` files |
| [`hooks`](.github/hooks) | Hook definitions and scripts |
| [`templates`](.github/templates) | Supporting review templates |

## Existing symbolic links

All four links currently point into this checkout:

```text
~/.copilot/agents
  -> /Users/pnagarajan/projects/personal/agent-box/vscode-prompts/.github/agents

~/.copilot/skills
  -> /Users/pnagarajan/projects/personal/agent-box/vscode-prompts/.github/skills

~/.copilot/hooks
  -> /Users/pnagarajan/projects/personal/agent-box/vscode-prompts/.github/hooks

~/.agent-box-toolkit/hooks
  -> /Users/pnagarajan/projects/personal/agent-box/vscode-prompts/.github/hooks
```

These are references to the repository, not copies. Repository updates are
therefore reflected in the linked directories.

## Current VS Code settings

The following relevant settings were found in the VS Code Insiders user settings:

```text
~/Library/Application Support/Code - Insiders/User/settings.json
```

```json
{
  "chat.instructionsFilesLocations": {
    ".github/instructions": true
  },
  "chat.hookFilesLocations": {
    "~/.agent-box-toolkit/hooks": true
  },
  "chat.useAgentSkills": true,
  "chat.useNestedAgentsMdFiles": true
}
```

This is an excerpt, not a replacement for the complete settings file. The
instructions location is workspace-relative; it does not point to this toolkit.

For regular VS Code on macOS, the equivalent user settings file is:

```text
~/Library/Application Support/Code/User/settings.json
```

Use **Preferences: Open User Settings (JSON)** in the editor you intend to use.

## Prompt file discovery

The prompt files live in [`.github/prompts`](.github/prompts).

No global prompt symlink or explicit `chat.promptFilesLocations` setting was found
in the inspected user configuration. The repository's documented approach is to
add `vscode-prompts` as a workspace folder:

**File > Add Folder to Workspace > select `vscode-prompts`**

Alternatively, include it in a multi-root workspace:

```json
{
  "folders": [
    { "path": "/path/to/your/project" },
    { "path": "/path/to/agent-box/vscode-prompts" }
  ]
}
```

No `.code-workspace` file was found within three levels of this repository root;
this snapshot does not establish which folders are mounted in other workspaces.

## Current hooks

VS Code is configured to discover hooks through `~/.agent-box-toolkit/hooks`.

| Definition | Events | Script |
|---|---|---|
| [`session-notifications.json`](.github/hooks/session-notifications.json) | `Stop` | `scripts/notify.sh` |
| [`story-attribution.json`](.github/hooks/story-attribution.json) | `SessionStart`, `Stop` | `scripts/emit-mapping.sh` |

Both definitions invoke scripts through the `~/.agent-box-toolkit/hooks` path.
Keep that link even when also creating `~/.copilot/hooks`.

The macOS notification hook requires:

```bash
brew install terminal-notifier
```

See the [hook documentation](.github/hooks/README.md) for notification permissions
and troubleshooting.

## Recreate on a new Mac

### 1. Clone the repository

```bash
mkdir -p "$HOME/projects/personal"
git clone https://github.com/prasann/agent-box.git \
  "$HOME/projects/personal/agent-box"
```

If already cloned, use the existing checkout.

### 2. Create the links

Adjust `SOURCE` if the checkout is elsewhere:

```bash
SOURCE="$HOME/projects/personal/agent-box/vscode-prompts/.github"

mkdir -p "$HOME/.copilot" "$HOME/.agent-box-toolkit"

ln -s "$SOURCE/agents" "$HOME/.copilot/agents"
ln -s "$SOURCE/skills" "$HOME/.copilot/skills"
ln -s "$SOURCE/hooks" "$HOME/.copilot/hooks"
ln -s "$SOURCE/hooks" "$HOME/.agent-box-toolkit/hooks"
```

Run these only when the destination paths do not already exist. Inspect and
preserve any existing configuration first. In particular, `ln -s` can create a
nested link if its destination is an existing directory.

### 3. Configure VS Code

1. Install VS Code or VS Code Insiders and enable GitHub Copilot.
2. Open **Preferences: Open User Settings (JSON)**.
3. Merge the relevant settings from the excerpt above into your existing settings.
4. Add the cloned `vscode-prompts` folder to the workspace for prompt discovery.
5. Install `terminal-notifier` if using the macOS notification hook.
6. Run **Developer: Reload Window**.

### 4. Verify

Inspect the links:

```bash
ls -ld "$HOME/.copilot/agents" \
  "$HOME/.copilot/skills" \
  "$HOME/.copilot/hooks" \
  "$HOME/.agent-box-toolkit/hooks"
```

Confirm that the targets exist:

```bash
ls "$HOME/.copilot/agents"
ls "$HOME/.copilot/skills"
ls "$HOME/.agent-box-toolkit/hooks"
```

In Copilot Chat, confirm that custom agents, skills, and workspace prompt files
are available. To test the notification script directly:

```bash
printf '%s\n' '{"hookEventName":"Stop"}' |
  bash "$HOME/.agent-box-toolkit/hooks/scripts/notify.sh"
```

This tests the script, not whether the editor has loaded the hook definitions.

## Portability notes

- Recreate the links on each laptop; they contain absolute paths on the current
  machine.
- Keep the checkout in place after creating the links.
- The notification setup is macOS-specific. Other operating systems need adapted
  link commands and notification scripts.
- Individual skills may require additional tools; follow their own `SKILL.md`
  instructions when using them.
 