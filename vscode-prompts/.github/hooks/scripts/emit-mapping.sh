#!/usr/bin/env bash
# emit-mapping.sh — Branch attribution hook for Copilot session tracking.
# Emits an OTLP log event mapping session_id → git branch → repo to localhost:4318.
# Safe to run even when the collector is not running (exits 0, no-op).

set -euo pipefail

INPUT=$(cat)

# Parse JSON fields from hook payload
HOOK_EVENT=$(echo "$INPUT" | grep -o '"hook_event_name"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4 || echo "")
SESSION_ID=$(echo "$INPUT" | grep -o '"session_id"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4 || echo "")
CWD=$(echo "$INPUT" | grep -o '"cwd"[[:space:]]*:[[:space:]]*"[^"]*"' | cut -d'"' -f4 || echo "")

LOG_DIR="${HOME}/.agent-box/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/branch-attribution.log"

log() { echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $*" >> "$LOG_FILE"; }

# Opt-out: per-session/shell kill switch
case "${COPILOT_BRANCH_TAGGING:-on}" in off|0|false)
    log "SKIP (COPILOT_BRANCH_TAGGING=off) $HOOK_EVENT"
    echo '{"continue": true}'; exit 0 ;;
esac

# Opt-out: machine-wide
if [[ -f "${HOME}/.copilot/branch-tagging.disabled" ]]; then
    log "SKIP (machine-wide disabled) $HOOK_EVENT"
    echo '{"continue": true}'; exit 0
fi

# Opt-out: per-repo
if [[ -n "$CWD" && -f "${CWD}/.copilot-otel-ignore" ]]; then
    log "SKIP (repo opt-out) $HOOK_EVENT [$CWD]"
    echo '{"continue": true}'; exit 0
fi

# Map hook event to OTLP event name
case "$HOOK_EVENT" in
    SessionStart) EVENT_NAME="branch.session.start" ;;
    *)
        log "SKIP (unhandled event) $HOOK_EVENT"
        echo '{"continue": true}'; exit 0 ;;
esac

# Homebrew is not on PATH in VS Code's non-login shell environment
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# Resolve branch and repo
REPO=$(basename "${CWD:-unknown}")
BRANCH_ID=$(git -C "$CWD" symbolic-ref --short HEAD 2>/dev/null || echo "")

if [[ -z "$BRANCH_ID" ]]; then
    log "SKIP (not a git repo or detached HEAD) $HOOK_EVENT [$REPO]"
    echo '{"continue": true}'; exit 0
fi

TIMESTAMP_NS="$(date -u +%s)000000000"

PAYLOAD=$(cat <<EOF
{
  "resourceLogs": [{
    "resource": {
      "attributes": [{"key": "service.name", "value": {"stringValue": "copilot-hooks"}}]
    },
    "scopeLogs": [{
      "scope": {"name": "branch-attribution", "version": "1.0"},
      "logRecords": [{
        "timeUnixNano": "$TIMESTAMP_NS",
        "severityText": "INFO",
        "body": {"stringValue": "$EVENT_NAME"},
        "attributes": [
          {"key": "event",      "value": {"stringValue": "$EVENT_NAME"}},
          {"key": "session.id", "value": {"stringValue": "$SESSION_ID"}},
          {"key": "branch.id",  "value": {"stringValue": "$BRANCH_ID"}},
          {"key": "repo.name",  "value": {"stringValue": "$REPO"}},
          {"key": "workspace",  "value": {"stringValue": "$CWD"}}
        ]
      }]
    }]
  }]
}
EOF
)

# DEBUG: log the payload being emitted for otel collector validation
log "EMIT $EVENT_NAME session=$SESSION_ID branch=$BRANCH_ID repo=$REPO"
log "PAYLOAD: $PAYLOAD"

# POST to collector — silent no-op if collector is not running
HTTP_STATUS=$(curl \
    --silent \
    --max-time 2 \
    --output /dev/null \
    --write-out "%{http_code}" \
    -X POST "http://localhost:4318/v1/logs" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" 2>/dev/null || echo "000")

if [[ "$HTTP_STATUS" == "200" ]]; then
    log "OK $EVENT_NAME session=$SESSION_ID branch=$BRANCH_ID repo=$REPO"
else
    log "WARN collector returned $HTTP_STATUS for $EVENT_NAME (collector may be down)"
fi

echo '{"continue": true}'
exit 0
