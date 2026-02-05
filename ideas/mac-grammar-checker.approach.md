# Mac Grammar/Typo Checker - Technical Approach

## Overview
Lightweight terminal-based tool to fix typos and grammar in copied text, with explicit rewrite mode. Uses Ollama (local LLM) for processing.

## User Flow

1. Copy text to clipboard (Cmd+C)
2. Run terminal command: `fix` or `rewrite`
3. Corrected text replaces clipboard
4. Paste back (Cmd+V)

**Use Cases**: 
- Browser-based apps (Gmail, web forms)
- Teams/Slack messages
- Any text input on Mac

**Frequency**: 1-2 times/day

## Architecture

```
┌─────────────────────────────┐
│  Clipboard (pbpaste/pbcopy) │
└──────────────┬──────────────┘
               │
               ▼
      ┌────────────────┐
      │  Python CLI    │
      │  (fix/rewrite) │
      └────────┬───────┘
               │
               ▼
         ┌──────────┐
         │  Ollama  │
         │  Local   │
         └──────────┘
```

## Implementation: Python CLI Tool

**Same structure as Gmail Cleaner** - consistent packaging, shared Ollama client.

### File Structure
```
mac-grammar-checker/
├── pyproject.toml          # Package definition + dependencies
├── README.md               # Setup + usage instructions
├── .gitignore
├── src/
│   └── grammar_checker/
│       ├── __init__.py
│       ├── __main__.py     # Entry points (fix, rewrite)
│       ├── checker.py      # Main logic
│       ├── ollama_client.py # Shared with gmail-cleaner
│       ├── clipboard.py    # macOS clipboard wrapper
│       ├── models.py       # Pydantic models
│       └── config.py       # Settings
```

### Dependencies (pyproject.toml)
```toml
[project]
name = "mac-grammar-checker"
version = "0.1.0"
dependencies = [
    "requests",
    "pydantic>=2.0",
    "pydantic-settings",
    "python-dotenv",
    "rich",  # For nice terminal output
]

[project.scripts]
fix = "grammar_checker.__main__:fix_main"
rewrite = "grammar_checker.__main__:rewrite_main"
```

### Core Code: `checker.py`

```python
"""Grammar and typo checker using Ollama."""
import subprocess
from typing import Literal
from .ollama_client import OllamaClient
from .models import CorrectionMode

class GrammarChecker:
    def __init__(self, ollama_client: OllamaClient):
        self.ollama = ollama_client
    
    def get_clipboard(self) -> str:
        """Get text from macOS clipboard."""
        result = subprocess.run(['pbpaste'], capture_output=True, text=True)
        return result.stdout
    
    def set_clipboard(self, text: str) -> None:
        """Set text to macOS clipboard."""
        subprocess.run(['pbcopy'], input=text.encode('utf-8'))
    
    def fix_grammar(self, text: str) -> str:
        """Fix only typos and grammar, preserve style."""
        prompt = f"""Fix ONLY typos and grammar errors in this text. Keep the style, tone, and structure exactly the same. Only fix clear mistakes.

Text:
{text}

Fixed text:"""
        
        response = self.ollama.generate(
            prompt=prompt,
            temperature=0.3  # Low temp for conservative fixes
        )
        return response.strip()
    
    def rewrite(self, text: str) -> str:
        """Full rewrite for clarity and professionalism."""
        prompt = f"""Rewrite this text to be clearer, more professional, and better structured. Fix grammar, improve word choice, and enhance readability.

Text:
{text}

Rewritten text:"""
        
        response = self.ollama.generate(
            prompt=prompt,
            temperature=0.7  # Higher temp for creative rewrite
        )
        return response.strip()
    
    def process_clipboard(self, mode: Literal["fix", "rewrite"], 
                         show_preview: bool = True) -> None:
        """Main workflow: clipboard → process → clipboard."""
        from rich.console import Console
        console = Console()
        
        # Get clipboard
        text = self.get_clipboard()
        if not text.strip():
            console.print("❌ Clipboard is empty", style="bold red")
            return
        
        # Process
        if mode == "fix":
            console.print("🔍 Checking grammar and typos...", style="bold blue")
            result = self.fix_grammar(text)
        else:
            console.print("✍️  Rewriting text...", style="bold blue")
            result = self.rewrite(text)
        
        # Set clipboard
        self.set_clipboard(result)
        console.print("✅ Copied to clipboard!", style="bold green")
        
        # Preview
        if show_preview:
            console.print("\n📋 Preview:", style="bold")
            console.print(result)
```

### Entry Points: `__main__.py`

```python
"""CLI entry points for fix and rewrite commands."""
import sys
from .checker import GrammarChecker
from .ollama_client import OllamaClient
from .config import Settings

def fix_main():
    """Entry point for 'fix' command."""
    settings = Settings()
    ollama = OllamaClient(
        model=settings.ollama_model,
        base_url=settings.ollama_url
    )
    checker = GrammarChecker(ollama)
    
    try:
        checker.process_clipboard(mode="fix")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

def rewrite_main():
    """Entry point for 'rewrite' command."""
    settings = Settings()
    ollama = OllamaClient(
        model=settings.ollama_model,
        base_url=settings.ollama_url
    )
    checker = GrammarChecker(ollama)
    
    try:
        checker.process_clipboard(mode="rewrite")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    fix_main()
```
**Exactly same as Gmail Cleaner**:

1. **Install Ollama** (if not already):
   ```bash
   brew install ollama
   ollama pull llama3.2:3b
   ```

2. **Install via pipx**:
   ```bash
   brew install pipx
   pipx ensurepath
   cd mac-grammar-checker
   pipx install .
   ```

3. **Test**:
   ```bash
   # Copy some text with typos, then:
   fix
   
   # Or for full rewrite:
   rewrite
   ```

That's it! The `fix` and `rewrite` commands are now in your PATH.
    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            requests.get(f"{self.base_url}/api/tags", timeout=2)
            return True
        except:
            return False
```

### Configuration: `config.py`

```python
"""Settings using Pydantic - consistent with gmail-cleaner."""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Ollama
    ollama_model: str = "llama3.2:3b"
    ollama_url: str = "http://localhost:11434"
    
    # Display
    show_preview: bool = True
    
    class Config:
        env_file = ".env"
        env_prefix = "GRAMMAR_CHECKER_"
```

## Setup Steps

1. **Install dependencies**:
   ```bash
   # jq for JSON parsing (if not already installed)
   brew install jq
   
   # Ensure Ollama is installed and running
   ollama pull llama3.2:3b
   ```

2. **Create script directory**:
   ```bash
   mkdir -p ~/.grammar-checker
   ```

3. **Create the script**:
   ```bash
   # Copy the fix.sh content above
   nano ~/.grammar-checker/fix.sh
   chmod +x ~/.grammar-checker/fix.sh
   ```

4. **Add to shell config**:
   ```bash
   echo 'source ~/.grammar-checker/fix.sh' >> ~/.zshrc
   source ~/.zshrc
   ```

5. **Test**:
   ```bash
   # Copy some text with typos, then:
   fix
   ```

## Usage Examples

```bash
# Scenario 1: Quick grammar fix
# 1. Copy: "i have an idee for one more agent"
# 2. Run:
fix
# 3. Output: "I have an idea for one more agent"
# 4. Paste back

# Scenario 2: Full rewrite
# 1. Copy: "gonna send this later probs"
# 2. Run:
rewrite
# 3. Output: "I will send this later, probably"
# 4. Paste back

# Scenario 3: See changes before applying
fixdiff
# Shows diff, asks for confirmation
```

```

### Advanced Options (Optional CLI Args)

```bash
# Disable preview
fixOptional: Global Hotkey (Hammerspoon)

If you want a hotkey instead of typing `fix`:

```lua
-- ~/.hammerspoon/init.lua
hs.hotkey.bind({"cmd", "shift"}, "G", function()
    hs.task.new("/usr/bin/fix", function(exitCode, stdOut, stdErr)
        if exitCode == 0 then
            hs.alert.show("✅ Grammar fixed!")
        end
    end):start()
end)

hs.hotkey.bind({"cmd", "shift"}, "R", function()
    hs.task.new("/usr/bin/rewrite", function(exitCode, stdOut, stdErr)
        if exitCode == 0 then
            hs.alert.show("✅ Text rewritten!")
        end
    end):start()
end)
```

**Setup
```

**Setup Hammerspoon**:
```bash
brew install --cask hammerspoon
# Add the Lua config above to ~/.hammerspoon/init.lua
```

## Configuration Options

**Environment Variables** (add to `~/.zshrc`):
```bash
# Override model
export GRAMMAR_CHECKER_MODEL="llama3.2:3b"

# Override Ollama URL (if usame pattern as Gmail Cleaner):
```bash
# Override model
export GRAMMAR_CHECKER_OLLAMA_MODEL="llama3.2:3b"

# Override Ollama URL
export GRAMMAR_CHECKER_OLLAMA_URL="http://localhost:11434"

# Show preview by default
export GRAMMAR_CHECKER_SHOW_PREVIEW="true"
```

Or use `.env` file in project root.bash
fix-tech() {
  Add custom modes** (future enhancement):
```bash
# Technical writing mode
fix --mode tech

# Casual chat mode
fix --mode casual

# Implementation: Add different prompts in checker.py# Performance

- **Local Ollama (llama3.2:3b)**: 
  - ~1-2 seconds for typical email/message
  - No internet required
  - Completely private
  
- **Response time breakdown**:
  - Clipboard read: <10ms
  - Ollama inference: 1-2 seconds
  - Clipboard write: <10ms
  - **Total**: ~1-2 seconds

## Alternative: GitHub Copilot Models API

If you prefer cloud-based (more accurate, but slower):

```bash
fix-gh() {
    local text=$(pbpaste)
    
    # Use GitHub Models API
    local response=$(gh api \
        -X POST /models/gpt-4o/chat/completions \
        -f model='gpt-4o' \
        -f messages[][role]='system' \
        -f messages[][content]='Fix only typos and grammar. Keep style unchanged.' \
        -f messages[][role]='user' \
        -f messages[][content]="$text" \
        --jq '.choices[0].message.content')
    
    echo "$response" | pbcopy
    echo "✅ Fixed with GPT-4o!"
}, can add GitHub Models support later:

```python
# Add to ollama_client.py as alternative backend
class GithubModelsClient:
    def generate(self, prompt: str) -> str:
        # Use gh CLI or direct API
        pass
```

**Pros of GitHub Models**:
- More accurate (GPT-4o)
- Free with Enterprise license

**Cons**:
- Slower (network latency)
- Text sent to cloud

**Recommendation**: Start with Ollama, add GitHub Models as fallback if needed
    
    # Rest of the fix logic...
}
```

## Clipboard Manager Integration

Since you use a clipboard manager (like Maccy, Paste, etc.):
- **Safe to overwrite**: Original text always in history
- **Quick undo**: Can retrieve original if needed
- **No backup needed**: Clipboard manager is your backup

## Estimated Development Time

- Create shell script: 30 minutes
- Test with different text types: 30 minutes
- Optional hotkey setup: 30 minutes
- **Total**: ~1-1.5 hours

## Why This Approach Works

✅ **Fast**: 1-2 seconds total (local LLM)  
✅ **Terminal-native**: No GUI, no menu bar app  
✅ **Always available**: Terminal always running  
✅ **Simple**: Just type `fix` or `rewrite`  
✅ *python
# In checker.py
def process_clipboard(self, ...):
    # Check Ollama availability
    if not self.ollama.is_available():
        console.print("❌ Error: Ollama is not running", style="bold red")
        console.print("Start it with: ollama serve", style="yellow")
        sys.exit(1)
    
    # Rest of logic with try/except Depends on Ollama running locally
- Quality depends on model choice
- Can't handle images/rich text (plain text only)

## Comparison to Grammarly

| Feature | This Solution | Grammarly |
|---------|---------------|-----------|
| Speed | 1-2s | Real-time |
| Privacy | 100% local | Cloud-based |
| Cost | Free | $12-15/month |
| Platform | Mac only | Cross-platform |
| Integration | Manual trigger | Auto-detect |
| Customization | Full control | Limited |
| Offline | Yes | No |

**Best for**: Privacy-conscious users who want manual control and are comfortable with terminal workflows.
Project setup (same as Gmail cleaner): 30 minutes
- Core checker logic: 1 hour
- CLI entry points: 30 minutes
- Testing: 1 hour
- **Total**: ~3 hours (includes proper structure)Python + Ollama (same as Gmail agent)  
✅ **Same packaging**: pipx install, same patterns  
✅ **Shared code**: Can reuse Ollama client, config patterns