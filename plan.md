# Mac Grammar Checker - Simplified Implementation Plan

## Problem Statement
Build a minimal terminal-based tool to fix typos/grammar in clipboard text using local Ollama LLM. Keep it extremely simple - just the core functionality.

## Approach
- Python CLI tool with two commands: `fix` and `rewrite`
- Uses clipboard (pbpaste/pbcopy) for input/output
- Local Ollama for processing (privacy + speed)
- Follow unified-agent-box structure for future integration

## Simplified Scope (MVP)
- ✅ Two commands only: `fix` (minimal changes) and `rewrite` (full rewrite)
- ✅ Direct clipboard integration (no preview, no options)
- ✅ Simple error handling
- ❌ No config files (hardcoded defaults)
- ❌ No preview mode
- ❌ No CLI options (keep it simple)
- ❌ No fancy output (basic prints)

## Workplan

### Phase 1: Project Setup
- [ ] Create agent-box root structure
- [ ] Create mac-grammar-checker directory structure
- [ ] Setup pyproject.toml with minimal dependencies
- [ ] Create .gitignore

### Phase 2: Core Implementation
- [ ] Implement Ollama client (simple, no retries)
- [ ] Implement clipboard wrapper (pbpaste/pbcopy)
- [ ] Implement checker logic (fix + rewrite)
- [ ] Create CLI entry points

### Phase 3: Testing & Validation
- [ ] Manual testing with sample text
- [ ] Verify Ollama integration works
- [ ] Test both fix and rewrite commands
- [ ] Ensure clipboard workflow works

### Phase 4: Documentation
- [ ] Add README with setup instructions
- [ ] Document usage examples

## Technical Details

### Directory Structure
```
agent-box/
├── README.md
├── pyproject.toml
└── agents/
    └── mac-grammar-checker/
        ├── README.md
        ├── pyproject.toml
        └── src/
            └── grammar_checker/
                ├── __init__.py
                ├── __main__.py      # Entry points
                ├── checker.py       # Main logic
                ├── clipboard.py     # Clipboard wrapper
                └── ollama_client.py # Simple Ollama client
```

### Minimal Dependencies
- requests (Ollama API)
- That's it!

### Key Simplifications
1. **No config system** - hardcode model="llama3.2:3b", url="http://localhost:11434"
2. **No preview** - just process and replace clipboard
3. **No CLI options** - two commands, that's it
4. **No error handling complexity** - just fail fast with simple messages
5. **No logging** - basic print statements
6. **No Pydantic models** - keep it simple

### Commands
```bash
# Install
pipx install ./agents/mac-grammar-checker

# Use
fix      # Fix typos/grammar only
rewrite  # Full rewrite
```

## Success Criteria
- [x] Can run `fix` command and clipboard gets corrected
- [x] Can run `rewrite` command and clipboard gets rewritten
- [x] Works with Ollama running locally
- [x] Takes <5 seconds end-to-end
- [x] Code is under 200 lines total

## Notes
- Start with absolute minimum viable product
- Can add features later (config, preview, options, etc.)
- Focus on getting it working quickly
- Follow structure that allows future integration into unified agent-box
