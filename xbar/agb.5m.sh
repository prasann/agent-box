#!/bin/bash

# <xbar.title>Agent Box</xbar.title>
# <xbar.version>v1.0</xbar.version>
# <xbar.author>Prasann Nagarajan</xbar.author>
# <xbar.author.github>prasann</xbar.author.github>
# <xbar.desc>Quick access to local AI productivity agents</xbar.desc>
# <xbar.dependencies>python3,gh</xbar.dependencies>
# <xbar.abouturl>https://github.com/prasann/agent-box</xbar.abouturl>

# Configuration - these get set by install script
VENV_PATH="$HOME/.local/share/agent-box/venv"
AGB_PATH="$VENV_PATH/bin/agb"
OLLAMA_URL="http://localhost:11434"
FULL_AGB_PATH="/Users/$USER/.local/share/agent-box/venv/bin/agb"

# Check if Ollama is running (needed for text/shell agents)
check_ollama() {
    curl -sf "${OLLAMA_URL}/api/tags" >/dev/null 2>&1
    return $?
}

# Check if GitHub CLI is authenticated (needed for FindTab)
check_gh_auth() {
    gh auth status >/dev/null 2>&1
    return $?
}

# Run command in iTerm2 (new tab if open, new window if not)
run_in_iterm() {
    local cmd="$1"
    osascript <<EOF
tell application "iTerm"
    activate
    if (count of windows) > 0 then
        tell current window
            create tab with default profile
            tell current session
                write text "$cmd"
            end tell
        end tell
    else
        set newWindow to (create window with default profile)
        tell current session of newWindow
            write text "$cmd"
        end tell
    end if
end tell
EOF
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
    if check_ollama || check_gh_auth; then
        echo "🤖"
    else
        echo "⚠️"
    fi
    
    echo "---"
    
    # Title
    echo "Agent Box | size=14 font=Menlo-Bold"
    echo "---"
    
    # Ollama status warning (for text/shell agents)
    if ! check_ollama; then
        echo "⚠️ Ollama Offline (text/shell agents) | color=orange"
        echo "--Start Ollama | bash='$HOME/.local/share/agent-box/venv/bin/python3' param1='-c' param2='import subprocess; subprocess.Popen([\"ollama\", \"serve\"])' terminal=false"
        echo "---"
    fi
    
    # GitHub auth status warning (for FindTab)
    if ! check_gh_auth; then
        echo "⚠️ GitHub CLI not authenticated | color=orange"
        echo "--Run: gh auth login | shell='$0' param1='iterm' param2='gh auth login' terminal=false refresh=false"
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
        echo "--Clean History | shell='$0' param1='iterm' param2='shell purge --preview' terminal=false refresh=false"
        echo "---"
    fi
    
    # FindTab Agent commands (if available)
    if "$AGB_PATH" findtab --help >/dev/null 2>&1; then
        if check_gh_auth; then
            echo "🔍 FindTab Agent"
            echo "--Search Tabs | shell='$0' param1='findtab-search' terminal=false refresh=false"
            echo "--Index Tabs | shell='$AGB_PATH' param1='findtab' param2='index' terminal=false refresh=true"
            echo "--Status | shell='$0' param1='iterm' param2='findtab status' terminal=false refresh=false"
        else
            echo "🔍 FindTab Agent (needs gh auth) | color=gray"
        fi
        echo "---"
    fi
    
    # System commands
    echo "⚙️ System"
    echo "--🔄 Refresh | refresh=true"
    echo "--📂 Open Project | bash='open' param1='$HOME/projects/personal/agent-box' terminal=false"
    echo "--📊 View Logs | shell='$0' param1='iterm' param2='tail -f $HOME/.local/state/ab/logs/agent-box.log' terminal=false refresh=false"
    echo "--🔧 Reinstall | shell='$0' param1='iterm' param2='$HOME/projects/personal/agent-box/install-xbar.sh' terminal=false refresh=false"
}

# Handle command execution
if [ "$1" = "run" ]; then
    run_agb_command "$2" "$3"
elif [ "$1" = "iterm" ]; then
    # Run any command in iTerm
    cmd="$2"
    # Replace $AGB_PATH placeholder with full path if present
    cmd="${cmd//\$AGB_PATH/$FULL_AGB_PATH}"
    # If it's an agb command, use full path
    if [[ "$cmd" == shell* ]] || [[ "$cmd" == findtab* ]] || [[ "$cmd" == text* ]]; then
        cmd="$FULL_AGB_PATH $cmd"
    fi
    run_in_iterm "$cmd"
elif [ "$1" = "findtab-search" ]; then
    # Prompt for search text using AppleScript
    search_text=$(osascript -e 'display dialog "Enter search text:" default answer "" with title "FindTab Search"' -e 'text returned of result' 2>/dev/null)
    if [ -n "$search_text" ]; then
        run_in_iterm "$FULL_AGB_PATH findtab search '$search_text'"
    fi
else
    main
fi
