#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd -P "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/agent-box-setup.XXXXXX")"
cleanup() {
    find "$TEST_ROOT" -type l -exec rm -- {} +
    find "$TEST_ROOT" -type f -exec rm -- {} +
    find "$TEST_ROOT" -depth -type d -exec rmdir -- {} +
}
trap cleanup EXIT

export HOME="$TEST_ROOT/home with spaces"
unset COPILOT_HOME
mkdir -p "$HOME"
INSTALLER="$REPO_DIR/install-copilot.sh"

expect_failure() {
    if bash "$INSTALLER" "$@" > "$TEST_ROOT/failure.log" 2>&1; then
        printf 'Expected failure: %s\n' "$*" >&2
        exit 1
    fi
}

bash "$INSTALLER" --dry-run
[[ ! -e "$HOME/.copilot" ]]
expect_failure --check

bash "$INSTALLER"
[[ "$(readlink "$HOME/.copilot/skills")" == "$REPO_DIR/vscode-prompts/.github/skills" ]]
[[ "$(readlink "$HOME/.copilot/agents")" == "$REPO_DIR/vscode-prompts/.github/agents" ]]
[[ ! -e "$HOME/.copilot/hooks" ]]
bash "$INSTALLER"
bash "$INSTALLER" --check
[[ ! -e "$REPO_DIR/vscode-prompts/.github/agents/agents" && ! -L "$REPO_DIR/vscode-prompts/.github/agents/agents" ]]

rm "$HOME/.copilot/skills" "$HOME/.copilot/agents"
mkdir "$HOME/.copilot/agents"
printf 'Keep me\n' > "$HOME/.copilot/agents/personal.agent.md"
expect_failure
[[ ! -e "$HOME/.copilot/skills" ]]
[[ -f "$HOME/.copilot/agents/personal.agent.md" ]]
bash "$INSTALLER" --dry-run --backup
[[ ! -e "$HOME/.copilot/skills" ]]
[[ -f "$HOME/.copilot/agents/personal.agent.md" ]]
bash "$INSTALLER" --backup
[[ -L "$HOME/.copilot/agents" ]]
[[ "$(find "$HOME/.copilot" -name personal.agent.md -type f | wc -l | tr -d ' ')" == 1 ]]

rm "$HOME/.copilot/skills"
ln -s "$TEST_ROOT/missing-source" "$HOME/.copilot/skills"
expect_failure
bash "$INSTALLER" --backup
bash "$INSTALLER" --check

export COPILOT_HOME="$TEST_ROOT/custom copilot home"
bash "$INSTALLER" --with-hooks
bash "$INSTALLER" --with-hooks --check
[[ "$(readlink "$COPILOT_HOME/hooks")" == "$REPO_DIR/vscode-prompts/.github/hooks" ]]
[[ "$(readlink "$HOME/.agent-box-toolkit/hooks")" == "$REPO_DIR/vscode-prompts/.github/hooks" ]]
[[ ! -e "$HOME/Library" ]]
bash "$REPO_DIR/install-hooks.sh" --check

FIXTURE="$TEST_ROOT/checkout with spaces"
mkdir -p "$FIXTURE/vscode-prompts/.github/skills" \
    "$FIXTURE/vscode-prompts/.github/agents" \
    "$FIXTURE/vscode-prompts/.github/hooks"
cp "$INSTALLER" "$FIXTURE/install-copilot.sh"
COPILOT_HOME="$TEST_ROOT/second machine" bash "$FIXTURE/install-copilot.sh"
COPILOT_HOME="$TEST_ROOT/second machine" bash "$FIXTURE/install-copilot.sh" --check
[[ "$(readlink "$TEST_ROOT/second machine/skills")" == "$FIXTURE/vscode-prompts/.github/skills" ]]

expect_failure --unknown
expect_failure --check --dry-run
COPILOT_HOME=relative expect_failure
printf '%s\n' 'All installer tests passed.'
