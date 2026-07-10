#!/bin/bash
# Install VS Code Copilot notification hooks
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOKS_SRC="${REPO_DIR}/vscode-prompts/.github/hooks"
HOOKS_DEST="${HOME}/.agent-box-toolkit/hooks"

echo "🔧 Installing Agent Box notification hooks..."
echo ""

# Create toolkit directory
echo "Creating toolkit directory..."
mkdir -p "${HOME}/.agent-box-toolkit"

# Create or update symlink
if [ -L "$HOOKS_DEST" ]; then
    echo "Removing existing symlink..."
    rm "$HOOKS_DEST"
elif [ -d "$HOOKS_DEST" ]; then
    echo "⚠️  Warning: $HOOKS_DEST exists as a directory"
    read -p "Replace it with symlink? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$HOOKS_DEST"
    else
        echo "❌ Installation cancelled"
        exit 1
    fi
fi

echo "Creating symlink: $HOOKS_DEST -> $HOOKS_SRC"
ln -sf "$HOOKS_SRC" "$HOOKS_DEST"

# Make scripts executable
echo "Making notification script executable..."
chmod +x "${HOOKS_DEST}/scripts/notify.sh"
chmod +x "${HOOKS_DEST}/scripts/emit-mapping.sh"

# Create logs directory
echo "Creating logs directory..."
mkdir -p "${HOME}/.agent-box/logs"

# Check VS Code settings
VSCODE_SETTINGS="${HOME}/Library/Application Support/Code/User/settings.json"
VSCODE_INSIDERS_SETTINGS="${HOME}/Library/Application Support/Code - Insiders/User/settings.json"

echo ""
echo "✅ Hooks installed successfully!"
echo ""
echo "📋 Next step: Configure VS Code"
echo ""
echo "Add this to your VS Code User Settings (Cmd+Shift+P → 'Preferences: Open User Settings (JSON)'):"
echo ""
echo '{'
echo '  "chat.hookFilesLocations": {'
echo '    "~/.agent-box-toolkit/hooks": true'
echo '  }'
echo '}'
echo ""

# Check if VS Code settings exist and offer to add config
if [ -f "$VSCODE_SETTINGS" ]; then
    echo "Found VS Code settings at: $VSCODE_SETTINGS"
    read -p "Would you like to add the configuration automatically? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Backup existing settings
        cp "$VSCODE_SETTINGS" "${VSCODE_SETTINGS}.backup.$(date +%Y%m%d_%H%M%S)"
        
        # Use Python to safely merge JSON (if available)
        if command -v python3 &> /dev/null; then
            python3 << 'EOF'
import json
import os

settings_path = os.path.expanduser("~/Library/Application Support/Code/User/settings.json")
with open(settings_path, 'r') as f:
    settings = json.load(f)

if 'chat.hookFilesLocations' not in settings:
    settings['chat.hookFilesLocations'] = {}

settings['chat.hookFilesLocations']['~/.agent-box-toolkit/hooks'] = True

with open(settings_path, 'w') as f:
    json.dump(settings, f, indent=2)

print("✅ VS Code settings updated!")
EOF
        else
            echo "⚠️  Python not found. Please add configuration manually."
        fi
    fi
elif [ -f "$VSCODE_INSIDERS_SETTINGS" ]; then
    echo "Found VS Code Insiders settings"
    echo "Please add the configuration manually to: $VSCODE_INSIDERS_SETTINGS"
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Test it:"
echo '  echo '"'"'{"hookEventName":"SessionStart","timestamp":"2026-03-10T10:30:00Z"}'"'"' | ~/.agent-box-toolkit/hooks/scripts/notify.sh'
echo ""
echo "📚 Read more: vscode-prompts/.github/hooks/README.md"
