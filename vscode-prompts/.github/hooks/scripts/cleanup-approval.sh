#!/usr/bin/env bash
# Clean up approval state when session ends
set -euo pipefail

INPUT=$(cat)

SESSION_ID=$(echo "$INPUT" | grep -o '"sessionId":"[^"]*"' | cut -d'"' -f4 || echo "")

# Clean up all approval state files for this session
STATE_DIR="${HOME}/.agent-box/approval-state"
if [ -d "$STATE_DIR" ]; then
    # Remove all state files (they're keyed by tool_use_id, not session_id)
    # This is safe because if a session ends, all pending approvals are invalid
    rm -f "$STATE_DIR"/*
    
    # Log cleanup
    LOG_DIR="${HOME}/.agent-box/logs"
    mkdir -p "$LOG_DIR"
    echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] SESSION_CLEANUP - Session: $SESSION_ID" >> "$LOG_DIR/notifications.log"
fi

echo '{"continue": true}'
exit 0
