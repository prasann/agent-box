#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$REPO_DIR/install-copilot.sh" --with-hooks "$@"
