# Simple Implementation Plan

> **Goal**: LLM-driven PR review with natural language refinement

**Timeline**: 3-4 days  
**Approach**: Keep it simple, let LLM do the work

---

## Day 1: Core Analysis Flow

**Task 1.1: Fetch & Parse PR** - Use gh CLI to get diff

**Task 1.2: Send to Copilot SDK** - Simple analysis call with prompt

**Task 1.3: Save to State File** - Simple JSON storage

---

## Day 2: Conversation Loop

**Task 2.1: Remove All Commands** - Delete commands.py, handlers.py

**Task 2.2: Build Conversation Context** - Natural language only

---

## Day 3: Polish & Integration

**Task 3.1: Posting Logic** - Format and post via gh CLI

**Task 3.2: Prompt Refinement** - Test with real PRs

**Task 3.3: UX Improvements** - Streaming, progress, formatting

---

## File Structure

```
src/pr_agent/
├── cli.py              # Entry point, 50 lines
├── analyzer.py         # PR analysis, 100 lines
├── repl.py            # Conversation loop, 100 lines
├── state.py           # State management, 50 lines
├── prompts.py         # Review prompts, 100 lines
└── gh_utils.py        # gh CLI wrapper, 50 lines

Total: ~450 lines of code
```

---

## Key Points

1. **No tools** - Just Copilot SDK chat
2. **Prompt-driven** - All logic in prompts
3. **Stateful** - JSON file tracks everything
4. **Natural** - Conversation, not commands
5. **Simple** - < 500 lines total

---

**Next Action**: Start with Day 1, Task 1.1 - fetch PR diff
