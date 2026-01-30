# Quick Start Guide - PR Review Agent

## 🚀 Get Started in 5 Minutes

### Step 1: Install Prerequisites

```bash
# Install GitHub CLI (if not already installed)
brew install gh

# Authenticate with GitHub
gh auth login

# Install Copilot CLI extension
gh extension install github/gh-copilot
```

### Step 2: Install PR Review Agent

```bash
cd agents/pr-review
bash scripts/install.sh
```

### Step 3: Try It Out!

```bash
# Navigate to any GitHub repository
cd ~/your-project

# Start reviewing a PR (replace 123 with actual PR number)
cd /path/to/agent-box/agents/pr-review
uv run pr-agent review 123

# Or activate the virtual environment first
source .venv/bin/activate
pr-agent review 123
```

## 💡 Example Questions to Ask

Once in the interactive session, try asking:

- "What are the main changes in this PR?"
- "Are there any security concerns?"
- "What files had the most changes?"
- "Can you explain the changes in auth.ts?"
- "Are there any potential bugs?"
- "Is error handling adequate?"
- "Are there breaking changes?"

## 📝 Common Commands

- `/help` - Show all available commands
- `/status` - View session information
- `/files` - List all changed files
- `/exit` - Save and exit

## 🎯 Phase 1 Capabilities

✅ **What Works Now:**
- Fetch and display PR information
- Interactive chat about the PR
- AI-powered code review assistance
- Session persistence
- Full PR context (metadata + diff)

⏳ **Coming in Future Phases:**
- Git history analysis
- Smart context selection
- Feedback accumulation
- Review generation
- Direct posting to GitHub

## 🐛 Troubleshooting

**Problem:** `gh CLI is not authenticated`  
**Solution:** Run `gh auth login`

**Problem:** `Copilot CLI not found`  
**Solution:** Run `gh extension install github/gh-copilot`

**Problem:** `Not in a git repository`  
**Solution:** Make sure you're in a directory with a Git repository

**Problem:** `PR #X not found`  
**Solution:** Verify the PR exists: `gh pr view X`

## 📚 Learn More

- See [PHASE1_COMPLETE.md](PHASE1_COMPLETE.md) for full documentation
- Check [docs/implementation_plan.md](docs/implementation_plan.md) for roadmap
- Read [docs/mvp_spec.md](docs/mvp_spec.md) for product vision

## 🎉 You're Ready!

That's it! You now have an AI-powered PR review assistant at your fingertips.

Try it out on your next PR and experience the future of code review! 🚀
