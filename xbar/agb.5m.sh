#!/bin/bash

# <xbar.title>Agent Box</xbar.title>
# <xbar.version>v1.0</xbar.version>
# <xbar.author>Prasann Nagarajan</xbar.author>
# <xbar.author.github>prasann</xbar.author.github>
# <xbar.desc>Quick access to local AI productivity agents</xbar.desc>
# <xbar.dependencies>python3,ollama</xbar.dependencies>
# <xbar.abouturl>https://github.com/prasann/agent-box</xbar.abouturl>

# Configuration - these get set by install script
VENV_PATH="$HOME/.local/share/agent-box/venv"
AGB_PATH="$VENV_PATH/bin/agb"
OLLAMA_URL="http://localhost:11434"

# Check if Ollama is running
check_ollama() {
    curl -sf "${OLLAMA_URL}/api/tags" >/dev/null 2>&1
    return $?
}

# Run agb command with notification
run_agb_command() {
    local cmd="$1"
    local title="Agent Box - $2"
    
    # Run in background with notifications
    (
        osascript -e "display notification \"Processing...\" with title \"$title\"" 2>/dev/null
        
        if "$AGB_PATH" $cmd --no-preview 2>&1; then
            osascript -e "display notification \"Done! Paste with Cmd+V\" with title \"$title\" sound name \"Glass\"" 2>/dev/null
        else
            osascript -e "display notification \"Error occurred\" with title \"$title\"" 2>/dev/null
        fi
    ) &
}

# Menu bar display
main() {
    # Check if venv exists
    if [ ! -f "$AGB_PATH" ]; then
        echo "⚠️"
        echo "---"
        echo "Agent Box Not Installed | color=red"
        echo "---"
        echo "Run installation script | bash='open' param1='-a' param2='Terminal' param3='$HOME/projects/personal/agent-box' terminal=false"
        return
    fi
    
    # Menu bar icon
    if check_ollama; then
        echo "🤖"
    else
        echo "⚠️"
    fi
    
    echo "---"
    
    # Title
    echo "Agent Box | size=14 font=Menlo-Bold"
    echo "---"
    
    # Ollama status warning
    if ! check_ollama; then
        echo "⚠️ Ollama Offline | color=red"
        echo "--Start Ollama | bash='$HOME/.local/share/agent-box/venv/bin/python3' param1='-c' param2='import subprocess; subprocess.Popen([\"ollama\", \"serve\"])' terminal=false"
        echo "---"
    fi
    
    # Text Agent commands
    echo "📝 Text Agent"
    echo "--Fix Grammar | shell='$0' param1='run' param2='text fix' param3='Grammar Fix' terminal=false refresh=false"
    echo "--Rewrite Text | shell='$0' param1='run' param2='text rewrite' param3='Rewrite' terminal=false refresh=false"
    echo "---"
    
    # Shell Agent commands (if available)
    if "$AGB_PATH" shell --help >/dev/null 2>&1; then
        echo "🐚 Shell Agent"
        echo "--Clean History | shell='$AGB_PATH' param1='shell' param2='purge' param3='--preview' terminal=true refresh=false"
        echo "---"
    fi
    
    # FindTab Agent commands (if available)
    if "$AGB_PATH" findtab --help >/dev/null 2>&1; then
        echo "🔍 FindTab Agent"
        echo "--Search Tabs | shell='$AGB_PATH' param1='findtab' param2='search' terminal=true refresh=false"
        echo "--Index Tabs | shell='$AGB_PATH' param1='findtab' param2='index' terminal=false refresh=true"
        echo "---"
    fi
    
    # System commands
    echo "⚙️ System"
    echo "--🔄 Refresh | refresh=true"
    echo "--📂 Open Project | bash='open' param1='$HOME/projects/personal/agent-box' terminal=false"
    echo "--📊 View Logs | bash='tail' param1='-f' param2='$HOME/.local/state/ab/logs/agent-box.log' terminal=true"
    echo "--🔧 Reinstall | bash='$HOME/projects/personal/agent-box/install-xbar.sh' terminal=true"
    echo "---"
    
    # About
    echo "ℹ️ About"
    echo "--Version: 1.0"
    echo "--Ollama: $(check_ollama && echo '✅ Online' || echo '❌ Offline')"
    echo "--GitHub | href=https://github.com/prasann/agent-box"
}

# Handle command execution
if [ "$1" = "run" ]; then
    run_agb_command "$2" "$3"
else
    main
fi
