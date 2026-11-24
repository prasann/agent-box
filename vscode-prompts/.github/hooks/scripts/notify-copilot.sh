#!/usr/bin/env bash
set -euo pipefail

export PATH="$PATH:/opt/homebrew/bin:/usr/local/bin"

# Native agentStop input has cwd but no hook_event_name.
CWD=$(python3 -c '
import json
import sys
payload = json.load(sys.stdin)
cwd = payload["cwd"]
if not isinstance(cwd, str) or not cwd:
    raise ValueError("agentStop cwd must be a non-empty string")
print(cwd)
')
REPO=$(basename "$CWD")

if osascript -e 'id of app "Visual Studio Code - Insiders"' &>/dev/null; then
    VSCODE_BUNDLE="com.microsoft.VSCodeInsiders"
else
    VSCODE_BUNDLE="com.microsoft.VSCode"
fi

TITLE="✅ Agent Done"
MESSAGE="Session complete — ready for your input"

if command -v terminal-notifier &>/dev/null; then
    terminal-notifier \
        -title "$TITLE" \
        -subtitle "$REPO" \
        -message "$MESSAGE" \
        -sound "Glass" \
        -group "${REPO}-Stop" \
        -activate "$VSCODE_BUNDLE" >/dev/null
else
    osascript - "$TITLE" "$REPO" "$MESSAGE" >/dev/null <<'APPLESCRIPT'
on run argv
    display notification (item 3 of argv) with title (item 1 of argv) subtitle (item 2 of argv)
end run
APPLESCRIPT
fi

LOG_DIR="${HOME}/.agent-box/logs"
mkdir -p "$LOG_DIR"
printf '[%s] agentStop [%s] - %s\n' \
    "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$REPO" "$MESSAGE" >> "$LOG_DIR/notifications.log"

printf '{}\n'
