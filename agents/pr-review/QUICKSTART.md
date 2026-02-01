# Quick Start Guide

## 🚀 Launch the App

```bash
cd /path/to/agent-box/agents/pr-review
uv run pr-agent
```

This will open the app at http://localhost:8501

---

## 📖 Step-by-Step

### 1. **Start from Your Repo**
```bash
cd ~/your-git-repo
# Make sure you have no uncommitted changes
git status
```

### 2. **Launch PR Agent**
```bash
# If you created the alias:
pr-agent

# Or run directly:
cd /path/to/agent-box/agents/pr-review && uv run pr-agent
```

### 3. **Analyze a PR**
- In the sidebar (left), enter a PR number
- Click "🔍 Analyze"
- Wait for analysis to complete (30-60 seconds)

### 4. **Review the Analysis**
**Left Panel:**
- Read the summary
- Review key findings
- No comments yet - they'll appear as you chat

**Right Panel:**
- See the initial analysis
- Ready to chat!

### 5. **Chat to Generate Comments**
Try asking:
- "Can you check the error handling in auth.py?"
- "What security concerns do you see?"
- "Are there any performance issues?"
- "Can you suggest improvements for the database queries?"

**Auto-extraction:** As the AI responds, if it provides structured comments (file:line format), they'll be automatically extracted and appear in the left panel!

### 6. **Review Comments**
**Left Panel - Comments Section:**
- Each comment shows:
  - 📍 File and line number
  - 💡 Code snippet (if available)
  - 💬 Detailed comment
  - 🎨 Severity: Issue (🔴), Suggestion (🟡), or Comment (🔵)
- Click to expand/collapse
- Edit or delete individual comments

### 7. **Export or Post**
- **📥 Export MD** - Download as markdown for manual posting
- **📤 Post to GitHub** - Coming soon! (will post all comments to PR)

### 8. **Continue Chatting**
- Ask follow-up questions
- Request clarifications
- Explore different aspects of the PR
- Comments continue to accumulate in the left panel

---

## 💡 Pro Tips

### Best Questions to Ask
- "Check [specific file] for [specific concern]"
- "Are there any edge cases not handled?"
- "What tests are missing?"
- "Compare this implementation with [other file]"
- "Is this pattern used consistently across the codebase?"

### Comment Extraction
The AI will automatically extract comments if you ask it to:
- "Generate review comments for this PR"
- "List issues with file and line numbers"
- "Provide structured feedback"

### Managing Comments
- **Edit** - Fix typos or refine wording
- **Delete** - Remove irrelevant comments
- **Export** - Save for later review
- **Clear All** - Start fresh

```
┌─────────────────────────────────────────────────────────┐
│ SIDEBAR          │ LEFT PANEL         │ RIGHT PANEL     │
│                  │                    │                 │
│ PR Selection     │ 📋 Summary         │ 💭 Chat History │
│ ┌─────────────┐  │ Summary text...    │ ┌─────────────┐ │
│ │ PR #: [123] │  │                    │ │ User: ...   │ │
│ │ [Analyze]   │  │ 🔍 Key Findings    │ │ AI: ...     │ │
│ └─────────────┘  │ • Finding 1        │ │ User: ...   │ │
│                  │ • Finding 2        │ │ AI: ...     │ │
│ ⚙️ Settings      │                    │ └─────────────┘ │
│ • Model          │ 💬 Comments (5)    │                 │
│ • Context        │ ┌────────────────┐ │ ┌─────────────┐ │
│                  │ │🔴 auth.py:42   │ │ │ Ask about   │ │
│ 📊 Status        │ │  Issue with... │ │ │ this PR...  │ │
│ ✅ PR #123       │ └────────────────┘ │ └─────────────┘ │
│ Comments: 5      │ ┌────────────────┐ │                 │
│                  │ │🟡 db.py:123    │ │                 │
│                  │ │  Suggest...    │ │                 │
│                  │ └────────────────┘ │                 │
│                  │                    │                 │
│                  │ 📤 Post to GitHub  │                 │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Comparison with Chainlit UI

| Feature | Streamlit | Chainlit |
|---------|-----------|----------|
| Leinstall dependencies
cd agents/pr-review
uv sync
```

### "Not in a git repository"
```bash
# Run from within a git repo
cd ~/your-git-repo
pr-agent
```

### "Repository has uncommitted changes"
```bash
# Commit or stash changes first
git status
git stash  # or git add . && git commit -m "..."
```

### Port already in use
```bash
# Use different port
uv run pr-agent --port 9000
```

---

## 🎯 Example Session

```bash
# Terminal
cd ~/my-project
pr-agent

# Browser opens at http://localhost:8501

# Sidebar: Enter PR number "42" → Click Analyze

# Wait 30 seconds...

# Left Panel shows:
# 📋 Summary: "This PR adds authentication..."
# 🔍 Key Findings:
#   • 3 files modified
#   • New auth middleware added
#   • Tests updated

# Right Panel (Chat):
You: "Check auth.py for security issues"

AI: "I've reviewed auth.py. Here are the security concerns:

**File**: src/auth.py
**Line**: 42
**Code**: `token = request.headers.get('token')`
**Comment**: Token should be validated before use. Missing input validation.
**Severity**: issue

**File**: src/auth.py
**Line**: 56
**Comment**: Consider using bcrypt for password hashing instead of SHA256.
**Severity**: suggestion
"

# Left Panel now shows 2 comments!

# Continue chatting or click "Export MD" to download
```

---

## 🎓 Next Steps

1. **Try it yourself** - Analyze a real PR
2. **Explore chat** - Ask different types of questions
3. **Review workflow** - See how comments accumulate
4. **Customize** - Adjust settings in sidebar
5. **Provide feedback** - What works? What could be better?

---

**Happy Reviewing! 🚀**

For more details, see [README.md](README.md) and [MIGRATION_PLAN.md](MIGRATION_PLAN.md)
