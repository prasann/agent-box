# xbar Plugin for Agent Box

🤖 Menu bar icon for one-click access to all AI agents.  

## Installation

**Prerequisites**: [xbar](https://xbarapp.com/), Ollama

```bash
# Install xbar (one-time)
brew install --cask xbar
# Open xbar, configure plugin directory

# Install plugin
./install-xbar.sh
```

**What it does:**
- Creates isolated venv at `~/.local/share/agent-box/venv`
- Installs `agb` CLI in editable mode
- Symlinks plugin to xbar directory

**Script is idempotent** - run anytime to update production with latest dev changes.

## Usage

**Daily workflow:**
1. Copy text (Cmd+C)
2. Click 🤖 → "Fix Grammar" or "Rewrite Text"
3. Wait for notification "Done!"
4. Paste result (Cmd+V)

**Menu structure:**
```
🤖
├── 📝 Text Agent
│   ├── Fix Grammar
│   └── Rewrite Text
├── ⚙️ System
│   ├── Refresh
│   ├── Open Project
│   └── View Logs
└── ℹ️ About
```

## Updating

**After making changes to agb:**
```bash
./install-xbar.sh  # Updates production venv
```

Code changes in editable mode take effect immediately, but run the installer to ensure dependencies are synced.

## Development

**Test plugin:**
```bash
./xbar/agb.5m.sh  # Should show xbar-formatted menu
```

**Test CLI:**
```bash
~/.local/share/agent-box/venv/bin/agb text fix
```

**Add new agent:**
- Implement in `agb/src/ab/agents/`
- Plugin auto-discovers from `--help` output
- Or manually add to `agb.5m.sh`

## Troubleshooting

**No 🤖 icon:**
- Open xbar → "Refresh All"
- Check: `ls -la ~/Library/.../xbar/plugins/agb.5m.sh`

**⚠️ icon (Ollama offline):**
```bash
ollama serve
```

**Commands fail:**
```bash
# Test directly
~/.local/share/agent-box/venv/bin/agb text fix

# Check logs
tail -f ~/.local/state/ab/logs/agent-box.log

# Reinstall
./install-xbar.sh
```

## Uninstall

```bash
rm -rf ~/.local/share/agent-box/venv
rm ~/Library/Application\ Support/xbar/plugins/agb.5m.sh
```

## Configuration

**Change icon:** Edit `echo "🤖"` in `agb.5m.sh`  
**Change refresh:** Rename to `agb.1m.sh` (1 min) or `agb.sh` (manual only)  
**View logs:** `tail -f ~/.local/state/ab/logs/agent-box.log`

---

**Learn more:** [xbar docs](https://xbarapp.com/) • [Agent Box](https://github.com/prasann/agent-box)
