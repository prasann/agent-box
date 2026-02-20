#!/bin/bash

# <xbar.title>Agent Box</xbar.title>
# <xbar.version>v1.0</xbar.version>
# <xbar.author>Prasann Nagarajan</xbar.author>
# <xbar.author.github>prasann</xbar.author.github>
# <xbar.desc>Quick access to AI productivity agents via GitHub Models</xbar.desc>
# <xbar.dependencies>python3,gh</xbar.dependencies>
# <xbar.abouturl>https://github.com/prasann/agent-box</xbar.abouturl>

# Load user environment for PATH and tokens
# xbar runs with minimal env, so we need to source the profile
if [ -f "$HOME/.zshrc" ]; then
    # Source non-interactively for env vars only
    export ZDOTDIR="$HOME"
    source "$HOME/.zshrc" 2>/dev/null || true
fi

# Ensure common paths are available
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

# Configuration - these get set by install script
VENV_PATH="$HOME/.local/share/agent-box/venv"
AGB_PATH="$VENV_PATH/bin/agb"
FULL_AGB_PATH="/Users/$USER/.local/share/agent-box/venv/bin/agb"
AGB_CONFIG="$HOME/.config/agent-box/env.sh"

# Load GitHub token from config file
if [ -f "$AGB_CONFIG" ]; then
    source "$AGB_CONFIG"
elif [ -z "$GITHUB_TOKEN" ]; then
    # Fallback: get from gh CLI and cache it
    GITHUB_TOKEN=$(gh auth token 2>/dev/null)
    export GITHUB_TOKEN
fi

# Check if GitHub CLI is authenticated (needed for all agents)
check_gh_auth() {
    gh auth status >/dev/null 2>&1
    return $?
}

# Run command in iTerm2 (new tab if open, new window if not)
run_in_iterm() {
    local cmd="$1"
    # Source the config file for GITHUB_TOKEN (if it exists)
    local source_cmd=""
    if [ -f "$AGB_CONFIG" ]; then
        source_cmd="source $AGB_CONFIG; "
    fi
    osascript <<EOF
tell application "iTerm"
    activate
    if (count of windows) > 0 then
        tell current window
            create tab with default profile
            tell current session
                write text "${source_cmd}$cmd"
            end tell
        end tell
    else
        set newWindow to (create window with default profile)
        tell current session of newWindow
            write text "${source_cmd}$cmd"
        end tell
    end if
end tell
EOF
}

# Run agb command with notification
run_agb_command() {
    local cmd="$1"
    local title="Agent Box - $2"
    
    # Add --no-preview only for text commands that support it
    local extra_args=""
    local done_msg="Done!"
    if [[ "$cmd" == text* ]]; then
        extra_args="--no-preview"
        done_msg="Done! Paste with Cmd+V"
    fi
    
    # Run in background with notifications (GITHUB_TOKEN inherited from env)
    (
        osascript -e "display notification \"Processing...\" with title \"$title\"" 2>/dev/null
        
        if "$AGB_PATH" $cmd $extra_args 2>&1; then
            osascript -e "display notification \"$done_msg\" with title \"$title\" sound name \"Glass\"" 2>/dev/null
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
    if check_gh_auth; then
        echo "🤖"
    else
        echo "⚠️"
    fi
    
    echo "---"
    
    # Title
    echo "Agent Box | size=14 font=Menlo-Bold"
    echo "---"
    
    # GitHub auth status warning (needed for all agents)
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
            echo "--Index Tabs | shell='$0' param1='run' param2='findtab index' param3='FindTab Index' terminal=false refresh=true"
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
