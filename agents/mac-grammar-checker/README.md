# Mac Grammar Checker

Simple terminal tool to fix typos and grammar in clipboard text using local Ollama.

## Features

- **fix**: Fix typos and grammar only (minimal changes)
- **rewrite**: Full rewrite for clarity and professionalism
- Privacy-first: Everything runs locally
- Fast: 1-2 seconds with Ollama
- Simple: Just two commands

## Prerequisites

1. **Install Ollama**:
   ```bash
   brew install ollama
   ```

2. **Pull model**:
   ```bash
   ollama pull llama3.2:3b
   ```

3. **Start Ollama** (if not running):
   ```bash
   ollama serve
   ```

## Installation

```bash
cd agents/mac-grammar-checker
pipx install .
```

## Usage

### Quick Fix
```bash
# 1. Copy text with typos (Cmd+C)
# 2. Run:
fix
# 3. Paste corrected text (Cmd+V)
```

### Full Rewrite
```bash
# 1. Copy text (Cmd+C)
# 2. Run:
rewrite
# 3. Paste rewritten text (Cmd+V)
```

## Examples

**Before (fix)**:
```
i have an idee for one more agent
```

**After (fix)**:
```
I have an idea for one more agent
```

**Before (rewrite)**:
```
gonna send this later probs
```

**After (rewrite)**:
```
I will send this later, probably
```

## How It Works

1. Reads text from clipboard (`pbpaste`)
2. Sends to local Ollama for processing
3. Writes result back to clipboard (`pbcopy`)
4. You paste with Cmd+V

## Troubleshooting

**"Cannot connect to Ollama"**:
```bash
ollama serve
```

**"Model not found"**:
```bash
ollama pull llama3.2:3b
```

## Customization

Edit model in `ollama_client.py`:
```python
OllamaClient(model="llama3.1:8b")  # Use larger model
```

## Performance

- **Speed**: ~1-2 seconds
- **Privacy**: 100% local (nothing sent to cloud)
- **Offline**: Works without internet
