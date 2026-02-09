# xbar Plugin for Agent Box - Technical Approach

## Overview
xbar menu bar plugin that provides quick access to all agent-box commands. One-click access to text fixing, rewrites, and future agents without opening terminal.

## User Experience

**Installation (one-time)**:
```bash
# Install both agb CLI and xbar plugin
cd agent-box
./install-xbar.sh
```

**Daily Usage**:
1. Click 🤖 in menu bar
2. Select action:
   - "Fix Grammar" → processes clipboard
   - "Rewrite Text" → processes clipboard
   - Future agents appear automatically
3. Get notification when done
4. Paste result (Cmd+V)

**Frequency**: Multiple times/day - faster than terminal commands

## Architecture

```
┌───────────────────────────┐
│   macOS Menu Bar (xbar)   │
│         🤖                 │
└──────────┬────────────────┘
           │
           ▼
┌──────────────────────────┐
│  agb.5m.py               │
│  (xbar plugin script)    │
│  - Lists commands        │
│  - Shows status          │
│  - Calls agb CLI         │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  agb CLI                 │
│  (existing package)      │
│  - text fix              │
│  - text rewrite          │
│  - [future agents]       │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Ollama (local)          │
└──────────────────────────┘
```

## Why xbar?

✅ **Always visible**: Menu bar icon always accessible  
✅ **One click**: Faster than Cmd+Space → Terminal → cd → agb  
✅ **Visual feedback**: See Ollama status at a glance  
✅ **Non-intrusive**: Hidden until you click  
✅ **Native macOS**: Feels like a system tool  
✅ **Simple**: Just a script calling existing CLI  

## Project Structure

```
agent-box/
├── agb/                        # Existing CLI package
│   ├── src/
│   │   └── ab/
│   │       ├── agents/
│   │       │   └── text/
│   │       │       └── commands.py
│   │       └── ...
│   └── pyproject.toml
│
├── xbar/                       # New: xbar plugin
│   ├── agb.5m.py              # Main plugin (Python)
│   ├── config.py              # Plugin settings
│   └── README.md              # Plugin docs
│
├── install-xbar.sh            # Installation script
├── README.md                  # Updated with xbar info
└── ...
```

## Implementation

### 1. xbar Plugin Script: `xbar/agb.5m.py`

**Filename format**: `agb.5m.py` = refresh every 5 minutes

```python
#!/usr/bin/env python3
"""
Agent Box xbar plugin - Quick access to AI agents.
<xbar.title>Agent Box</xbar.title>
<xbar.version>v1.0</xbar.version>
<xbar.author>Prasann</xbar.author>
<xbar.author.github>prasann</xbar.author.github>
<xbar.desc>Quick access to local AI agents</xbar.desc>
<xbar.dependencies>python3,ollama</xbar.dependencies>
<xbar.abouturl>https://github.com/prasann/agent-box</xbar.abouturl>
"""

import subprocess
import sys
import json
from pathlib import Path

# Configuration
AGB_PATH = "/Users/pnagarajan/.local/bin/agb"  # pipx install location
OLLAMA_URL = "http://localhost:11434"

def check_ollama_status():
    """Check if Ollama is running."""
    try:
        result = subprocess.run(
            ["curl", "-s", f"{OLLAMA_URL}/api/tags"],
            capture_output=True,
            timeout=2
        )
        return result.returncode == 0
    except:
        return False

def run_agb_command(command, show_notification=True):
    """Run agb command in background."""
    bash_script = f"""
    osascript -e 'display notification "Processing..." with title "Agent Box"'
    {AGB_PATH} {command} --no-preview
    if [ $? -eq 0 ]; then
        osascript -e 'display notification "Done! Paste with Cmd+V" with title "Agent Box" sound name "Glass"'
    else
        osascript -e 'display notification "Error - check terminal" with title "Agent Box"'
    fi
    """
    
    subprocess.Popen(
        ["bash", "-c", bash_script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def get_agb_commands():
    """Get available agb commands by parsing help output."""
    try:
        result = subprocess.run(
            [AGB_PATH, "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # Parse commands from help output
        # This is a simple parser - could be more sophisticated
        commands = []
        if "text" in result.stdout:
            commands.append(("text", [
                ("fix", "Fix Grammar", "text fix"),
                ("rewrite", "Rewrite Text", "text rewrite")
            ]))
        
        return commands
    except:
        return []

def main():
    """Main plugin output."""
    
    # Check Ollama status
    ollama_running = check_ollama_status()
    
    # Menu bar icon + title
    if ollama_running:
        print("🤖")  # Menu bar icon
    else:
        print("⚠️")  # Warning icon if Ollama offline
    
    print("---")  # Separator
    
    # Main menu
    print("Agent Box | size=14")
    print("---")
    
    if not ollama_running:
        print("⚠️ Ollama Offline | color=red")
        print("Start Ollama | bash='ollama serve' terminal=true")
        print("---")
    
    # Text Agent commands
    print("📝 Text Agent")
    print("--Fix Grammar | bash='python3' param1='{}' param2='fix' terminal=false refresh=false".format(__file__))
    print("--Rewrite Text | bash='python3' param1='{}' param2='rewrite' terminal=false refresh=false".format(__file__))
    
    # Get additional commands dynamically (for future agents)
    commands = get_agb_commands()
    if len(commands) > 1:  # More than just text agent
        print("---")
        for agent_name, agent_commands in commands:
            if agent_name != "text":  # Already showed text
                print(f"🔧 {agent_name.title()} Agent")
                for cmd_name, cmd_label, cmd_full in agent_commands:
                    print(f"--{cmd_label} | bash='python3' param1='{__file__}' param2='{cmd_full}' terminal=false refresh=false")
    
    print("---")
    
    # System commands
    print("🔄 Refresh | refresh=true")
    print("⚙️ Settings")
    print("--Open Terminal | bash='open' param1='-a' param2='Terminal' terminal=false")
    print("--View Logs | bash='tail' param1='-f' param2='$HOME/Library/Logs/agent-box.log' terminal=true")
    print("---")
    print("ℹ️ About")
    print("--Agent Box v1.0 | href=https://github.com/prasann/agent-box")
    print(f"--Ollama: {'✅ Online' if ollama_running else '❌ Offline'}")

if __name__ == "__main__":
    # If called with a command argument, run it
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])
        run_agb_command(command)
    else:
        main()
```

### 2. Simpler Shell Version: `xbar/agb.5m.sh`

If you prefer pure shell (lighter weight):

```bash
#!/bin/bash

# <xbar.title>Agent Box</xbar.title>
# <xbar.version>v1.0</xbar.version>
# <xbar.author>Prasann</xbar.author>
# <xbar.desc>Quick access to local AI agents</xbar.desc>

AGB_PATH="/Users/pnagarajan/.local/bin/agb"
OLLAMA_URL="http://localhost:11434"

# Check Ollama status
check_ollama() {
    curl -s "${OLLAMA_URL}/api/tags" >/dev/null 2>&1
    return $?
}

# Run command with notification
run_with_notification() {
    local cmd="$1"
    local title="$2"
    
    osascript -e "display notification \"Processing...\" with title \"$title\""
    
    if $AGB_PATH $cmd --no-preview; then
        osascript -e "display notification \"Done! Paste with Cmd+V\" with title \"$title\" sound name \"Glass\""
    else
        osascript -e "display notification \"Error - check logs\" with title \"$title\""
    fi
}

# Main menu output
if check_ollama; then
    echo "🤖"
else
    echo "⚠️"
fi

echo "---"
echo "Agent Box | size=14"
echo "---"

# Check Ollama
if ! check_ollama; then
    echo "⚠️ Ollama Offline | color=red"
    echo "Start Ollama | bash='ollama' param1='serve' terminal=true"
    echo "---"
fi

# Text Agent
echo "📝 Text Agent"
echo "--Fix Grammar | shell='$AGB_PATH' param1='text' param2='fix' param3='--no-preview' terminal=false refresh=false"
echo "--Rewrite Text | shell='$AGB_PATH' param1='text' param2='rewrite' param3='--no-preview' terminal=false refresh=false"

echo "---"

# Future agents go here automatically
# Gmail, Calendar, etc. - just add more echo statements

# System
echo "🔄 Refresh | refresh=true"
echo "⚙️ Settings"
echo "--Open Terminal | bash='open' param1='-a' param2='Terminal' terminal=false"
echo "--Open agb Directory | bash='open' param1='$HOME/projects/personal/agent-box' terminal=false"

echo "---"
echo "ℹ️ About | href=https://github.com/prasann/agent-box"
```

### 3. Installation Script: `install-xbar.sh`

```bash
#!/bin/bash
set -e

echo "🤖 Agent Box + xbar Installation"
echo "================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "Checking prerequisites..."

# 1. Check for pipx
if ! command -v pipx &> /dev/null; then
    echo -e "${YELLOW}Installing pipx...${NC}"
    brew install pipx
    pipx ensurepath
fi

# 2. Check for Ollama
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}Installing Ollama...${NC}"
    brew install ollama
    
    echo -e "${YELLOW}Pulling llama3.2:3b model...${NC}"
    ollama pull llama3.2:3b
fi

# 3. Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo -e "${YELLOW}Starting Ollama...${NC}"
    ollama serve &
    sleep 2
fi

# 4. Install agb CLI
echo -e "${GREEN}Installing agb CLI...${NC}"
cd agb
pipx install --force .
cd ..

# 5. Check for xbar
if [ ! -d "/Applications/xbar.app" ]; then
    echo -e "${YELLOW}Installing xbar...${NC}"
    brew install --cask xbar
    
    echo ""
    echo -e "${YELLOW}⚠️  xbar installed! Please:${NC}"
    echo "   1. Open xbar from Applications"
    echo "   2. Choose plugin directory when prompted"
    echo "   3. Run this script again"
    exit 0
fi

# 6. Install xbar plugin
XBAR_PLUGIN_DIR="$HOME/Library/Application Support/xbar/plugins"

# Try to find xbar plugin directory
if [ ! -d "$XBAR_PLUGIN_DIR" ]; then
    # Check alternative location
    XBAR_PLUGIN_DIR=$(defaults read com.matryer.xbar pluginDirectory 2>/dev/null || echo "")
    
    if [ -z "$XBAR_PLUGIN_DIR" ] || [ ! -d "$XBAR_PLUGIN_DIR" ]; then
        echo -e "${RED}Could not find xbar plugin directory.${NC}"
        echo "Please:"
        echo "  1. Open xbar"
        echo "  2. Click xbar menu → Preferences → Plugins..."
        echo "  3. Note the plugin directory path"
        echo "  4. Run: ln -s $(pwd)/xbar/agb.5m.sh '<plugin-directory>/agb.5m.sh'"
        exit 1
    fi
fi

echo -e "${GREEN}Installing xbar plugin...${NC}"

# Create plugin directory if needed
mkdir -p "$XBAR_PLUGIN_DIR"

# Symlink plugin (so updates to repo affect plugin)
ln -sf "$(pwd)/xbar/agb.5m.sh" "$XBAR_PLUGIN_DIR/agb.5m.sh"
chmod +x "$XBAR_PLUGIN_DIR/agb.5m.sh"

# Update plugin with correct paths
sed -i '' "s|AGB_PATH=.*|AGB_PATH=\"$(which agb)\"|" "$XBAR_PLUGIN_DIR/agb.5m.sh"

echo ""
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Click the 🤖 icon in your menu bar"
echo "  2. Copy some text (Cmd+C)"
echo "  3. Select 'Fix Grammar' or 'Rewrite Text'"
echo "  4. Paste result (Cmd+V)"
echo ""
echo "Troubleshooting:"
echo "  • If no menu bar icon: Open xbar.app and click 'Refresh All'"
echo "  • If ⚠️ icon: Start Ollama with 'ollama serve'"
echo "  • View logs: tail -f ~/Library/Logs/agent-box.log"
```

### 4. Plugin Configuration: `xbar/config.py`

For Python plugin to load settings:

```python
"""Configuration for xbar plugin."""
from pathlib import Path

# Paths
AGB_CLI = Path.home() / ".local/bin/agb"
OLLAMA_URL = "http://localhost:11434"

# UI Settings
SHOW_NOTIFICATIONS = True
REFRESH_INTERVAL = "5m"  # 5 minutes

# Commands to show (beyond auto-detected)
PINNED_COMMANDS = [
    ("📝 Fix Grammar", "text fix"),
    ("✍️ Rewrite Text", "text rewrite"),
]
```

## Enhanced Features

### 1. Smart Command Detection

Auto-detect new agents from `agb --help`:

```python
def discover_agents():
    """Dynamically discover available agents."""
    result = subprocess.run(
        [AGB_PATH, "--help"],
        capture_output=True,
        text=True
    )
    
    # Parse agent groups from help output
    agents = {}
    current_agent = None
    
    for line in result.stdout.split('\n'):
        if 'Commands:' in line:
            continue
        if line.strip() and not line.startswith(' '):
            # New agent group
            parts = line.split()
            if len(parts) >= 2:
                agent_name = parts[0]
                agents[agent_name] = []
                current_agent = agent_name
    
    return agents
```

### 2. Recent History

Show last 3 operations:

```python
def show_history():
    """Show recent operations."""
    history_file = Path.home() / ".config/agent-box/history.json"
    
    if history_file.exists():
        with open(history_file) as f:
            history = json.load(f)
        
        print("📜 Recent")
        for item in history[-3:]:
            timestamp = item['timestamp']
            command = item['command']
            print(f"--{timestamp}: {command}")
```

### 3. Keyboard Shortcuts

xbar supports custom keyboard shortcuts:

```bash
# In plugin output
echo "--Fix Grammar | bash='...' shortcut='cmd+shift+g'"
echo "--Rewrite Text | bash='...' shortcut='cmd+shift+r'"
```

### 4. Status Indicators

Change icon based on state:

```python
def get_menu_icon():
    """Get appropriate menu bar icon."""
    if not check_ollama_status():
        return "⚠️"  # Ollama offline
    
    # Check if processing
    if is_processing():
        return "⚙️"  # Processing
    
    return "🤖"  # Ready
```

### 5. Error Handling

Show errors in menu:

```bash
if ! $AGB_PATH text fix --no-preview 2>/dev/null; then
    echo "❌ Last operation failed | color=red"
    echo "--View error log | bash='tail' param1='-20' param2='~/.local/state/ab/logs/agent-box.log' terminal=true"
fi
```

## Usage Workflows

### Workflow 1: Quick Grammar Fix
1. Copy text in browser (Cmd+C)
2. Click 🤖 → "Fix Grammar"
3. See notification "Processing..."
4. Wait 1-2 seconds
5. Get notification "Done!"
6. Paste (Cmd+V)

### Workflow 2: Email Rewrite
1. Draft email in Gmail web
2. Select all text (Cmd+A) → Copy (Cmd+C)
3. Click 🤖 → "Rewrite Text"
4. Wait for notification
5. Paste rewritten text (Cmd+V)
6. Review and send

### Workflow 3: Check Status
1. Click 🤖
2. See: "Ollama: ✅ Online"
3. Or: "⚠️ Ollama Offline" → Click "Start Ollama"

## Adding New Agents

When you add a new agent (e.g., Gmail), the plugin **automatically** detects it:

```bash
# Add gmail agent to agb CLI
agb/src/ab/agents/gmail/commands.py

# Plugin automatically shows:
# 📧 Gmail Agent
#   --Clean Inbox
#   --Mark Spam
```

**Manual addition** (if auto-detection doesn't work):

```bash
# Edit xbar/agb.5m.sh, add:
echo "📧 Gmail Agent"
echo "--Clean Inbox | shell='$AGB_PATH' param1='gmail' param2='clean' param3='--dry-run' terminal=false"
```

## Installation Steps (User Perspective)

### One-Time Setup
```bash
# Clone repo (if not already)
git clone https://github.com/prasann/agent-box.git
cd agent-box

# Run installation script
./install-xbar.sh

# That's it! 🤖 appears in menu bar
```

### Updating
```bash
# Pull latest changes
cd agent-box
git pull

# Reinstall (picks up new agents)
./install-xbar.sh
```

**Plugin auto-updates** because it's symlinked to repo!

## Configuration

### Environment Variables

Add to `~/.zshrc`:

```bash
# xbar plugin settings
export AGB_XBAR_SHOW_NOTIFICATIONS=true
export AGB_XBAR_REFRESH_INTERVAL="5m"
export AGB_OLLAMA_URL="http://localhost:11434"
```

### Custom Icons

Edit in `xbar/agb.5m.sh`:

```bash
# Change menu bar icon
echo "🧠"  # Instead of 🤖

# Change agent icons
echo "✏️ Text Agent"     # Instead of 📝
echo "📮 Gmail Agent"    # Instead of 📧
```

## xbar Plugin Metadata

Required for xbar plugin directory:

```bash
# <xbar.title>Agent Box</xbar.title>
# <xbar.version>v1.0</xbar.version>
# <xbar.author>Prasann</xbar.author>
# <xbar.author.github>prasann</xbar.author.github>
# <xbar.desc>Quick access to local AI productivity agents</xbar.desc>
# <xbar.image>https://github.com/prasann/agent-box/raw/main/docs/xbar-screenshot.png</xbar.image>
# <xbar.dependencies>python3,ollama</xbar.dependencies>
# <xbar.abouturl>https://github.com/prasann/agent-box</xbar.abouturl>
```

## Testing

### Test Plugin Syntax
```bash
# Test plugin output
./xbar/agb.5m.sh

# Should output xbar-formatted menu
```

### Test Commands
```bash
# Manually trigger command
/Users/pnagarajan/.local/bin/agb text fix --no-preview

# Check exit code
echo $?  # Should be 0
```

### Test in xbar
1. Open xbar
2. Click 🤖
3. Select "Fix Grammar"
4. Check notification appears
5. Check clipboard has result

## Performance Considerations

- **Refresh interval**: 5 minutes is sufficient (status rarely changes)
- **Command execution**: Happens in background (non-blocking)
- **Startup time**: <100ms (just displays menu, no heavy operations)
- **Memory**: ~5MB (persistent xbar daemon)

## Comparison to Terminal Commands

| Aspect | Terminal (`agb text fix`) | xbar Plugin |
|--------|---------------------------|-------------|
| **Speed to invoke** | 3-5 seconds | 1 click |
| **Visual feedback** | Terminal output | Notifications |
| **Always available** | Need terminal open | Always in menu bar |
| **Discoverability** | Must remember commands | Browse menu |
| **Status check** | Run `curl` manually | Visual icon |
| **Learning curve** | Medium | Low |

**Recommendation**: Use both! Terminal for scripting/automation, xbar for quick interactive use.

## Alternative: Alfred Workflow

If you prefer Alfred:

```bash
# Alfred workflow file
tell application "System Events"
    set clipboardText to the clipboard as text
    do shell script "/Users/pnagarajan/.local/bin/agb text fix --no-preview"
    delay 2
    display notification "Grammar fixed!" with title "Agent Box"
end tell
```

**Pros of Alfred**:
- Keyboard-first
- More flexible workflows
- Can show rich previews

**Cons**:
- Requires Alfred Powerpack ($$$)
- More complex to set up

**Recommendation**: Start with xbar (free, simpler), consider Alfred later.

## Troubleshooting

### Plugin not showing
```bash
# Check xbar is running
ps aux | grep xbar

# Check plugin directory
defaults read com.matryer.xbar pluginDirectory

# Refresh manually
# Click xbar menu → "Refresh All"
```

### ⚠️ Icon (Ollama offline)
```bash
# Start Ollama
ollama serve

# Or add to startup
# System Settings → Users & Groups → Login Items → Add ollama
```

### Commands not working
```bash
# Test agb CLI directly
/Users/pnagarajan/.local/bin/agb text fix

# Check permissions
ls -la ~/.local/bin/agb
# Should be executable (rwxr-xr-x)

# Check logs
tail -f ~/.local/state/ab/logs/agent-box.log
```

### Plugin not updating
```bash
# Plugin is symlinked, so should auto-update
# Force refresh:
touch xbar/agb.5m.sh
# Click xbar menu → "Refresh All"
```

## Development Time Estimate

- Basic shell plugin: 1 hour
- Installation script: 1 hour
- Testing & polish: 1 hour
- Documentation: 30 minutes
- **Total**: ~3-4 hours

## Future Enhancements

### Phase 1 (Current)
- [x] Basic menu with text commands
- [x] Ollama status indicator
- [x] Notifications on completion
- [x] Installation script

### Phase 2 (Future)
- [ ] Command history in menu
- [ ] Keyboard shortcuts
- [ ] Processing indicator (spinner)
- [ ] Error messages in menu
- [ ] Settings submenu

### Phase 3 (Advanced)
- [ ] Rich previews (show diff)
- [ ] Undo last operation
- [ ] Multiple profiles (formal/casual)
- [ ] Usage statistics

## Why This Works

✅ **Zero learning curve**: Click menu, select action  
✅ **Always accessible**: Menu bar always visible  
✅ **Non-intrusive**: Small icon, dropdown only when needed  
✅ **Fast**: One click vs terminal workflow  
✅ **Visual**: Icons, status, notifications  
✅ **Discoverable**: New commands appear automatically  
✅ **Maintainable**: Simple script calling existing CLI  
✅ **Flexible**: Easy to add new features  

## Complementary to Terminal

xbar doesn't replace the terminal - it complements it:

**Use xbar for**:
- Quick interactive fixes
- Checking status
- Discovering commands

**Use terminal for**:
- Scripting/automation
- Batch operations
- Development/testing
- Detailed output/logs

Both use the same `agb` CLI under the hood!

## Summary

This xbar plugin makes agent-box significantly more useful for daily workflows:

1. **Simple**: Just a bash/Python script
2. **In-repo**: Lives in `agent-box/xbar/`
3. **Easy install**: One script sets up everything
4. **Auto-expanding**: New agents appear automatically
5. **Maintainable**: Calls existing CLI (no duplication)
6. **Fast**: 1 click instead of terminal workflow

**Estimated value**: Saves ~30 seconds per use × 5-10 uses/day = **2-5 minutes/day**

Over a year: ~15-30 hours saved! 🎉
