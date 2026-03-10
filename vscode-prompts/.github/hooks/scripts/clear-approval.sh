#!/usr/bin/env bash
# Clear approval state when PostToolUse fires (tool executed successfully)
set -euo pipefail

INPUT=$(cat)

TOOL_USE_ID=$(echo "$INPUT" | grep -o '"tool_use_id":"[^"]*"' | cut -d'"' -f4 || echo "")

# Skip if no tool_use_id
if [ -z "$TOOL_USE_ID" ]; then
    echo '{"continue": true}'
    exit 0
fi

# Remove state file to cancel approval notification
STATE_FILE="${HOME}/.agent-box/approval-state/${TOOL_USE_ID}"
if [ -f "$STATE_FILE" ]; then
    rm -f "$STATE_FILE"
fi

echo '{"continue": true}'
exit 0
