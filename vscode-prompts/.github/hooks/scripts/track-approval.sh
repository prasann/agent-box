#!/usr/bin/env bash
# Track PreToolUse events and check for pending approvals
set -euo pipefail

INPUT=$(cat)

TOOL_USE_ID=$(echo "$INPUT" | grep -o '"tool_use_id":"[^"]*"' | cut -d'"' -f4 || echo "")
TOOL_NAME=$(echo "$INPUT" | grep -o '"tool_name":"[^"]*"' | cut -d'"' -f4 || echo "")

# Skip if no tool_use_id
if [ -z "$TOOL_USE_ID" ]; then
    echo '{"continue": true}'
    exit 0
fi

# Only track tools that typically require approval
case "$TOOL_NAME" in
    create_file|replace_string_in_file|multi_replace_string_in_file|run_in_terminal|edit_notebook_file)
        # Track this tool invocation
        STATE_DIR="${HOME}/.agent-box/approval-state"
        mkdir -p "$STATE_DIR"
        
        STATE_FILE="${STATE_DIR}/${TOOL_USE_ID}"
        TRANSCRIPT_PATH=$(echo "$INPUT" | grep -o '"transcript_path":"[^"]*"' | cut -d'"' -f4 || echo "")
        
        echo "$TOOL_NAME" > "$STATE_FILE"
        echo "$(date +%s)" >> "$STATE_FILE"
        echo "$TRANSCRIPT_PATH" >> "$STATE_FILE"
        
        # Spawn background checker with progressive notifications
        (
            WAIT_TIMES=(15 45 120)  # 15s, 45s (30s later), 2m (75s later)
            NOTIFICATION_COUNT=0
            
            for WAIT in "${WAIT_TIMES[@]}"; do
                sleep "$WAIT"
                
                # Check if state file still exists
                if [ ! -f "$STATE_FILE" ]; then
                    # Tool completed, exit
                    exit 0
                fi
                
                TOOL=$(sed -n '1p' "$STATE_FILE")
                START_TIME=$(sed -n '2p' "$STATE_FILE")
                TRANSCRIPT=$(sed -n '3p' "$STATE_FILE")
                CURRENT_TIME=$(date +%s)
                ELAPSED=$((CURRENT_TIME - START_TIME))
                
                # Check if transcript was modified recently (agent activity)
                if [ -f "$TRANSCRIPT" ]; then
                    TRANSCRIPT_MTIME=$(stat -f %m "$TRANSCRIPT" 2>/dev/null || stat -c %Y "$TRANSCRIPT" 2>/dev/null || echo "$START_TIME")
                    TIME_SINCE_MODIFIED=$((CURRENT_TIME - TRANSCRIPT_MTIME))
                    
                    # If transcript modified in last 5s, agent is active, skip notification
                    if [ "$TIME_SINCE_MODIFIED" -lt 5 ]; then
                        continue
                    fi
                fi
                
                NOTIFICATION_COUNT=$((NOTIFICATION_COUNT + 1))
                
                # Send approval notification with elapsed time
                if [ "$NOTIFICATION_COUNT" -eq 1 ]; then
                    TITLE="⚠️ Approval Needed"
                    MESSAGE="Tool: $TOOL"
                    SOUND="Ping"
                elif [ "$NOTIFICATION_COUNT" -eq 2 ]; then
                    TITLE="⚠️ Still Waiting"
                    MESSAGE="Tool: $TOOL (${ELAPSED}s)"
                    SOUND="Ping"
                else
                    TITLE="⏳ Still Pending"
                    MESSAGE="Tool: $TOOL (${ELAPSED}s)"
                    SOUND="Funk"
                fi
                
                osascript -e "display notification \"$MESSAGE\" with title \"$TITLE\" sound name \"$SOUND\""
                
                # Log it
                LOG_DIR="${HOME}/.agent-box/logs"
                mkdir -p "$LOG_DIR"
                echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] APPROVAL_PENDING (${ELAPSED}s) - Tool: $TOOL" >> "$LOG_DIR/notifications.log"
            done
            
            # Clean up state file after final notification
            rm -f "$STATE_FILE"
        ) &
        ;;
    *)
        # Don't track read-only tools
        ;;
esac

echo '{"continue": true}'
exit 0
