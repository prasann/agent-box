#!/usr/bin/env bash
# macOS notification script for VS Code Copilot hooks
# Uses terminal-notifier for persistent alerts with click-to-focus

set -euo pipefail

INPUT=$(cat)

# Parse JSON fields (VS Code sends snake_case)
HOOK_EVENT=$(echo "$INPUT" | grep -o '"hook_event_name"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4 || echo "Unknown")
CWD=$(echo "$INPUT" | grep -o '"cwd"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4 || echo "")
AGENT_TYPE=$(echo "$INPUT" | grep -o '"agent_type"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4 || echo "")

REPO=$(basename "${CWD:-unknown}")

# Detect VS Code variant (Insiders takes priority)
if osascript -e 'id of app "Visual Studio Code - Insiders"' &>/dev/null 2>&1; then
    VSCODE_BUNDLE="com.microsoft.VSCodeInsiders"
else
    VSCODE_BUNDLE="com.microsoft.VSCode"
fi

case "$HOOK_EVENT" in
    Stop)
        TITLE="✅ Agent Done"
        SUBTITLE="$REPO"
        MESSAGE="Session complete — ready for your input"
        SOUND="Glass"
        ;;
    SubagentStop)
        TITLE="🎯 Subagent Done"
        SUBTITLE="$REPO"
        MESSAGE="${AGENT_TYPE:-Subagent} complete"
        SOUND="Pop"
        ;;
    *)
        LOG_DIR="${HOME}/.agent-box/logs"
        mkdir -p "$LOG_DIR"
        echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] SKIP $HOOK_EVENT" >> "$LOG_DIR/notifications.log"
        echo '{"continue": true}'
        exit 0
        ;;
esac

# Homebrew is not on PATH in VS Code's non-login shell environment
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# Send persistent notification
if command -v terminal-notifier &>/dev/null; then
    # -group:    replaces previous notification for same repo+event (no pile-up)
    # -activate: clicking the notification focuses VS Code
    terminal-notifier \
        -title "$TITLE" \
        -subtitle "$SUBTITLE" \
        -message "$MESSAGE" \
        -sound "$SOUND" \
        -group "${REPO}-${HOOK_EVENT}" \
        -activate "$VSCODE_BUNDLE"
else
    osascript -e "display notification \"$MESSAGE\" with title \"$TITLE\" subtitle \"$SUBTITLE\""
fi

LOG_DIR="${HOME}/.agent-box/logs"
mkdir -p "$LOG_DIR"
echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $HOOK_EVENT [$REPO] - $MESSAGE" >> "$LOG_DIR/notifications.log"

echo '{"continue": true}'
exit 0
