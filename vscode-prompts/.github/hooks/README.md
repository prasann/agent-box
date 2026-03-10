# Hooks — macOS Notifications

Native macOS notifications for VS Code Copilot agent lifecycle events, using [`terminal-notifier`](https://github.com/julienXX/terminal-notifier).

## What fires

| Event | Notification | When |
|---|---|---|
| `Stop` | ✅ Agent Done | Agent finished its turn, waiting for your input |

The subtitle shows the **repo name** so you always know which project to switch to. Clicking the notification focuses VS Code.

## Requirements

```bash
brew install terminal-notifier
```

For persistent (non-dismissing) alerts: **System Settings → Notifications → terminal-notifier** → set style to **Alert**.

## Installation

From the repo root:

```bash
./install-hooks.sh
```

Add to VS Code user settings (`Cmd+Shift+P` → `Preferences: Open User Settings JSON`):

```json
{
  "chat.hookFilesLocations": {
    "~/.agent-box-toolkit/hooks": true
  }
}
```

Then reload VS Code (`Developer: Reload Window`).

## Hook Files

Enable/disable notifications by adding/removing these files:

| File | Events | Purpose |
|------|--------|---------|
| `session-notifications.json` | SessionStart, Stop | Main session lifecycle |
| `subagent-notifications.json` | SubagentStart, SubagentStop | Track subagent spawning |
| `prompt-notifications.json` | UserPromptSubmit | Every prompt submission |

**To disable a notification type:** Rename or delete the corresponding `.json` file.

## Customization

### Change Notification Appearance

Edit [scripts/notify.sh](scripts/notify.sh) to customize titles, messages, and sounds per event:

```bash
case "$HOOK_EVENT" in
    SessionStart)
        TITLE="🤖 Agent Session Started"
        MESSAGE="New Copilot session initialized"
        SOUND="Glass"  # macOS sound name
        ;;
    # ... more events
esac
```

Available macOS sounds: `Basso`, `Blow`, `Bottle`, `Frog`, `Funk`, `Glass`, `Hero`, `Morse`, `Ping`, `Pop`, `Purr`, `Sosumi`, `Submarine`

Run `ls /System/Library/Sounds/` to see all available sounds.

### View Notification Log

All notifications are logged to `~/.agent-box/logs/notifications.log`:

```bash
tail -f ~/.agent-box/logs/notifications.log
```

## Phone Notifications (Coming Soon)

The script includes a placeholder for phone notifications. To enable:

1. **Choose a service:**
   - [ntfy.sh](https://ntfy.sh/) - Free, open source, self-hostable
   - [Pushover](https://pushover.net/) - $5 one-time, iOS/Android
   - [Telegram Bot API](https://core.telegram.org/bots/api) - Free

2. **Create config:**
```bash
mkdir -p ~/.agent-box/config
nano ~/.agent-box/config/phone-notify.sh
```

3. **Example for ntfy.sh:**
```bash
send_to_phone() {
    local title="$1"
    local message="$2"
    curl -s -d "$message" \
        -H "Title: $title" \
        -H "Priority: low" \
        ntfy.sh/your-unique-topic
}
```

4. **Uncomment in notify.sh** (lines 73-76)

## Troubleshooting

### Notifications not showing

1. **Check VS Code loaded the hooks:**
   - View → Output → Select "GitHub Copilot Chat Hooks"
   - Look for "Load Hooks" messages

2. **Test notification manually:**
   ```bash
   echo '{"hookEventName":"SessionStart","timestamp":"2026-03-10T10:30:00Z"}' | \
       ~/.agent-box-toolkit/hooks/scripts/notify.sh
   ```

3. **Check macOS notification permissions:**
   - System Settings → Notifications → VS Code
   - Ensure "Allow Notifications" is enabled

### Script not executable

```bash
chmod +x ~/.agent-box-toolkit/hooks/scripts/notify.sh
```

### Symlink broken

```bash
# Remove old link
rm ~/.agent-box-toolkit/hooks

# Recreate from agent-box repo
cd /path/to/agent-box
ln -sf "$(pwd)/vscode-prompts/.github/hooks" ~/.agent-box-toolkit/hooks
```

## Advanced Usage

### Project-Specific Overrides

Add a `.github/hooks/` directory to any project to override or extend global hooks:

```
my-project/
└── .github/
    └── hooks/
        └── custom-notifications.json  # Project-specific hooks
```

Workspace hooks run **in addition to** global hooks.

### Agent-Scoped Notifications

Add hooks to specific agents in their YAML frontmatter:

```yaml
---
name: My Agent
hooks:
  Stop:
    - type: command
      command: "osascript -e 'display notification \"Agent complete\" with title \"My Agent\"'"
---
```

Requires `chat.useCustomAgentHooks: true` in VS Code settings.

### Disable Specific Events

To disable only SessionStart notifications, edit `session-notifications.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "type": "command",
        "command": "bash ~/.agent-box-toolkit/hooks/scripts/notify.sh",
        "timeout": 5
      }
    ]
  }
}
```

## Example Notifications

**Session Start:**
```
🤖 Agent Session Started
New Copilot session initialized
```

**Subagent Spawned:**
```
🔄 Subagent Started
Agent: AGB - Implementer
```

**Session Complete:**
```
✅ Agent Session Complete
Copilot session finished
```

## Related

- [VS Code Hooks Documentation](https://code.visualstudio.com/docs/copilot/customization/hooks)
- [Agents](../agents/) - Custom agent definitions
- [Skills](../skills/) - Reusable agent skills
