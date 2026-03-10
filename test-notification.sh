#!/bin/bash
# Test notification system
# Usage: ./test-notification.sh [event_name]

EVENT="${1:-SessionStart}"

echo "🧪 Testing notification for event: $EVENT"
echo ""

SCRIPT="${HOME}/.agent-box-toolkit/hooks/scripts/notify.sh"

if [ ! -f "$SCRIPT" ]; then
    echo "❌ Notification script not found at: $SCRIPT"
    echo "Run ./install-hooks.sh first"
    exit 1
fi

if [ ! -x "$SCRIPT" ]; then
    echo "❌ Script not executable. Running: chmod +x $SCRIPT"
    chmod +x "$SCRIPT"
fi

case "$EVENT" in
    SessionStart)
        JSON='{"hookEventName":"SessionStart","timestamp":"2026-03-10T10:30:00Z","sessionId":"test-123","cwd":"/test"}'
        ;;
    Stop)
        JSON='{"hookEventName":"Stop","timestamp":"2026-03-10T10:30:00Z","sessionId":"test-123","cwd":"/test"}'
        ;;
    SubagentStart)
        JSON='{"hookEventName":"SubagentStart","timestamp":"2026-03-10T10:30:00Z","sessionId":"test-123","agent_type":"AGB - Implementer","agent_id":"sub-456","cwd":"/test"}'
        ;;
    SubagentStop)
        JSON='{"hookEventName":"SubagentStop","timestamp":"2026-03-10T10:30:00Z","sessionId":"test-123","agent_type":"AGB - Implementer","agent_id":"sub-456","cwd":"/test"}'
        ;;
    PreToolUse)
        JSON='{"hookEventName":"PreToolUse","timestamp":"2026-03-10T10:30:00Z","sessionId":"test-123","tool_name":"replace_string_in_file","tool_use_id":"tool-789","cwd":"/test"}'
        ;;
    PostToolUse)
        JSON='{"hookEventName":"PostToolUse","timestamp":"2026-03-10T10:30:00Z","sessionId":"test-123","tool_name":"replace_string_in_file","tool_use_id":"tool-789","cwd":"/test"}'
        ;;
    UserPromptSubmit)
        JSON='{"hookEventName":"UserPromptSubmit","timestamp":"2026-03-10T10:30:00Z","sessionId":"test-123","prompt":"test prompt","cwd":"/test"}'
        ;;
    PreCompact)
        JSON='{"hookEventName":"PreCompact","timestamp":"2026-03-10T10:30:00Z","sessionId":"test-123","trigger":"auto","cwd":"/test"}'
        ;;
    *)
        echo "❌ Unknown event: $EVENT"
        echo ""
        echo "Available events:"
        echo "  SessionStart, Stop, SubagentStart, SubagentStop"
        echo "  PreToolUse, PostToolUse, UserPromptSubmit, PreCompact"
        exit 1
        ;;
esac

echo "Sending: $JSON"
echo ""

echo "$JSON" | "$SCRIPT"

echo ""
echo "✅ Test complete! Check your macOS notifications."
echo ""
echo "View log:"
echo "  tail ~/.agent-box/logs/notifications.log"
