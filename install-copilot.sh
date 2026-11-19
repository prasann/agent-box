#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COPILOT_DIR="${COPILOT_HOME:-${HOME}/.copilot}"
DRY_RUN=false
CHECK=false
BACKUP=false
WITH_HOOKS=false

usage() {
    cat <<'EOF'
Usage: ./install-copilot.sh [--dry-run | --check] [--backup] [--with-hooks]

Link this checkout's skills and agents into ${COPILOT_HOME:-~/.copilot}.
  --dry-run     Show planned changes without writing anything.
  --check       Verify all requested links; exit 1 if setup is incomplete.
  --backup      Move conflicting files, directories, or links aside first.
  --with-hooks  Also link hooks (macOS completion notifications).
  --help        Show this help.

Existing correct links are preserved. Conflicts stop installation unless
--backup is supplied. No editor settings, dependencies, or credentials change.
EOF
}

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --check) CHECK=true ;;
        --backup) BACKUP=true ;;
        --with-hooks) WITH_HOOKS=true ;;
        --help|-h) usage; exit 0 ;;
        *) printf 'Unknown option: %s\n' "$arg" >&2; usage >&2; exit 2 ;;
    esac
done

if $DRY_RUN && $CHECK; then
    printf '%s\n' '--dry-run and --check cannot be combined.' >&2
    exit 2
fi

if [[ "$COPILOT_DIR" != /* ]]; then
    printf 'Copilot home must be absolute: %s\n' "$COPILOT_DIR" >&2
    exit 2
fi

sources=(
    "$REPO_DIR/vscode-prompts/.github/skills"
    "$REPO_DIR/vscode-prompts/.github/agents"
)
destinations=("$COPILOT_DIR/skills" "$COPILOT_DIR/agents")

if $WITH_HOOKS; then
    sources+=(
        "$REPO_DIR/vscode-prompts/.github/hooks"
        "$REPO_DIR/vscode-prompts/.github/hooks"
    )
    destinations+=("$COPILOT_DIR/hooks" "$HOME/.agent-box-toolkit/hooks")
    printf '%s\n' \
        'Hooks requested: completion notifications require macOS.' \
        'Remove the legacy chat.hookFilesLocations entry for ~/.agent-box-toolkit/hooks' \
        'from editor settings when using native Copilot discovery to avoid duplicate hooks.'
fi

correct_link() {
    [[ -L "$1" && -d "$1" ]] && [[ "$(cd -P "$1" && pwd)" == "$2" ]]
}

failed=false
for ((i = 0; i < ${#sources[@]}; i++)); do
    source_dir="${sources[$i]}"
    destination="${destinations[$i]}"
    if [[ ! -d "$source_dir" ]]; then
        printf 'Missing source: %s\n' "$source_dir" >&2
        failed=true
    elif correct_link "$destination" "$source_dir"; then
        printf 'OK: %s -> %s\n' "$destination" "$source_dir"
    elif [[ -e "$destination" || -L "$destination" ]]; then
        printf 'Conflict: %s\n' "$destination" >&2
        if $CHECK || ! $BACKUP; then
            failed=true
        fi
    elif $CHECK; then
        printf 'Missing link: %s\n' "$destination" >&2
        failed=true
    fi
done

if $failed; then
    printf '%s\n' 'Setup incomplete. No changes made. Use --backup to preserve and replace conflicts.' >&2
    exit 1
fi
$CHECK && exit 0

for ((i = 0; i < ${#sources[@]}; i++)); do
    source_dir="${sources[$i]}"
    destination="${destinations[$i]}"
    if correct_link "$destination" "$source_dir"; then
        continue
    fi
    if $DRY_RUN; then
        printf 'Would link: %s -> %s\n' "$destination" "$source_dir"
        if [[ -e "$destination" || -L "$destination" ]]; then
            printf 'Would back up existing destination first: %s\n' "$destination"
        fi
        continue
    fi
    mkdir -p "$(dirname "$destination")"
    if [[ -e "$destination" || -L "$destination" ]]; then
        backup="${destination}.backup.$(date +%Y%m%d_%H%M%S).$$"
        while [[ -e "$backup" || -L "$backup" ]]; do
            backup="${backup}.old"
        done
        mv "$destination" "$backup"
        printf 'Backed up: %s -> %s\n' "$destination" "$backup"
    fi
    ln -s "$source_dir" "$destination"
    printf 'Linked: %s -> %s\n' "$destination" "$source_dir"
done

if ! $DRY_RUN; then
    printf '%s\n' 'Setup complete. Start a fresh Copilot session to load customizations.'
fi
