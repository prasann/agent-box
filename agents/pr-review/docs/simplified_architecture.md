# Simplified Architecture Flow

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│  User runs: pr-agent 123                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  cli.py (32 lines)                                           │
│  • Parse PR number                                           │
│  • Create ReviewREPL instance                                │
│  • Start async event loop                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  repl.py (195 lines)                                         │
│  • Initialize PRAnalyzer and ReviewState                     │
│  • Check for existing session                                │
│  • If new: trigger auto-analysis                             │
│  • If resume: load conversation                              │
│  • Start conversation loop                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  analyzer.py (123 lines)                                     │
│  • Fetch PR data via gh_utils.py                             │
│  • Build prompts via prompts.py                              │
│  • Initialize Copilot client                                 │
│  • Send analysis request                                     │
│  • Save to state via state.py                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  Conversation Loop (in repl.py)                              │
│                                                               │
│  User Input → Process → AI Response → Display → Repeat       │
│                                                               │
│  Commands:                                                   │
│  • Natural question → analyzer._chat() → response            │
│  • /post → generate review → confirm → gh_utils.post()       │
│  • /comment → generate review → confirm → gh_utils.post()    │
│  • /exit → save state → cleanup                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
                ┌────┴────┐
                │  Done!   │
                └─────────┘
```

## Module Responsibilities

```
┌─────────────────────────────────────────────────────────────┐
│  cli.py                                                      │
│  └─ Entry point, argument parsing, async coordination        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  repl.py                                                     │
│  └─ Conversation loop, command handling, user interaction    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  analyzer.py                                                 │
│  └─ Copilot integration, PR analysis, chat coordination      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  state.py                                                    │
│  └─ JSON file management, conversation & comment storage     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  prompts.py                                                  │
│  └─ System prompts, analysis prompts, formatting helpers     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  gh_utils.py                                                 │
│  └─ GitHub CLI wrappers (fetch PR, post review/comment)      │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

```
                    ┌──────────────┐
                    │   GitHub     │
                    │   (via gh)   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  PR Data     │
                    │  & Diff      │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌──────────────┐  ┌──────────────┐
│   prompts.py  │  │  analyzer.py │  │   state.py   │
│               │  │              │  │              │
│ Format for AI │◄─┤   Copilot    │──►│  Save JSON   │
└───────────────┘  │   Client     │  │              │
                   └──────┬───────┘  └──────────────┘
                          │
                   ┌──────▼───────┐
                   │  AI Response │
                   └──────┬───────┘
                          │
                   ┌──────▼───────┐
                   │   Display    │
                   │   (Rich)     │
                   └──────────────┘
```

## State File Structure

```json
{
  "pr_number": 123,
  "conversation": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "comments": [
    {
      "file": "src/auth.py",
      "line": 42,
      "comment": "...",
      "severity": "issue"
    }
  ],
  "metadata": {
    "pr_info": {...},
    "diff": "..."
  }
}
```

## Command Flow Examples

### Initial Analysis
```
pr-agent 123
    ↓
gh_utils.get_pr_info(123)
    ↓
gh_utils.get_pr_diff(123)
    ↓
prompts.build_initial_prompt()
    ↓
analyzer._chat(messages)
    ↓
Display analysis
    ↓
Wait for user input
```

### Natural Question
```
User: "Check error handling in auth.py"
    ↓
state.add_message("user", question)
    ↓
analyzer._chat(conversation)
    ↓
state.add_message("assistant", response)
    ↓
Display response
```

### Post Review
```
User: /post
    ↓
prompts.COMMENT_GENERATION_PROMPT
    ↓
analyzer._chat(conversation)
    ↓
Display formatted review
    ↓
Confirm with user
    ↓
gh_utils.post_pr_review()
    ↓
Success message
```

## Key Simplifications

1. **No Command Parser**: Just 3 commands (`/post`, `/comment`, `/exit`)
2. **No Complex Models**: Plain dicts and JSON
3. **No Context Builder**: Direct PR data from `gh CLI`
4. **No Session Manager**: Simple file-based state
5. **No Feedback System**: LLM generates comments naturally

## Philosophy

> "Make it work, make it simple, make it obvious"

- Single responsibility per file
- Direct function calls, no abstractions
- Let the LLM handle complexity
- JSON for all state
- `gh CLI` for all GitHub ops
