# Migration Plan: Chainlit → Streamlit

## Objective
Migrate PR Review Agent from Chainlit to Streamlit to enable a 2-panel layout with persistent review summary, comments, and chat interface.

---

## Why Migrate?

**Current Limitations (Chainlit):**
- ❌ No native 2-panel layout
- ❌ Single-column chat flow only
- ❌ Hard to maintain persistent side panels
- ❌ Not ideal for structured data display

**Streamlit Benefits:**
- ✅ Native multi-column layouts
- ✅ Perfect for review workflow (summary + chat)
- ✅ Better state management
- ✅ Easy to display structured data (comments)
- ✅ Keep all backend logic unchanged

---

## Architecture Comparison

### Current (Chainlit)
```
app.py (Chainlit)
├── on_chat_start() → Initialize PR analysis
├── on_message() → Handle chat
└── on_chat_end() → Cleanup

UI: Single column chat
```

### New (Streamlit)
```
streamlit_app.py
├── Sidebar: PR selection & config
├── Left Panel (30%):
│   ├── Review Summary
│   ├── Key Findings
│   ├── Comments List
│   └── Post to GitHub button
└── Right Panel (70%):
    ├── Chat History
    └── Chat Input

Backend: Keep analyzer.py, prompts, repo_utils unchanged
```

---

## What Changes / What Stays

### ✅ Keep Unchanged (No Changes Needed)
- `src/analyzer.py` - PR analysis logic
- `src/prompts.py` - Prompt utilities
- `src/prompt_loader.py` - Prompty integration
- `src/repo_utils.py` - Git operations
- `src/gh_utils.py` - GitHub CLI wrapper
- `src/state.py` - State management
- `prompts/` - All prompt files
- Backend Copilot SDK integration

### 🔄 Replace
- `app.py` (Chainlit) → `streamlit_app.py` (Streamlit)
- `.chainlit/config.toml` → Streamlit config in code

### ➕ Add New
- `src/ui/` - UI components
  - `sidebar.py` - Sidebar configuration
  - `review_panel.py` - Left panel (summary/comments)
  - `chat_panel.py` - Right panel (chat)
- `src/comment_store.py` - Comment state management
- `src/comment_extractor.py` - Extract comments from LLM responses

### 🗑️ Can Remove
- `app.py` - Replace with streamlit_app.py
- `.chainlit/` directory - No longer needed
- `chainlit.md` - No longer needed

---

## Migration Steps

### **Phase 1: Setup (30 min)**

#### 1.1 Add Streamlit Dependency
```bash
cd agents/pr-review
uv add streamlit
```

**Update pyproject.toml:**
```toml
dependencies = [
    "streamlit>=1.40.0",  # Add this
    # ... keep existing
]
```

#### 1.2 Create New Directory Structure
```bash
mkdir -p src/ui
touch src/ui/__init__.py
touch src/ui/sidebar.py
touch src/ui/review_panel.py
touch src/ui/chat_panel.py
touch src/comment_store.py
touch src/comment_extractor.py
```

---

### **Phase 2: Core Components (1 hour)**

#### 2.1 Comment Store (`src/comment_store.py`)
**Purpose:** Manage comments list with file operations

```python
from dataclasses import dataclass
from typing import List
import json

@dataclass
class Comment:
    file: str
    line: int
    code_snippet: str
    comment: str
    severity: str  # 'issue' | 'suggestion' | 'comment'

class CommentStore:
    def __init__(self, pr_number: int):
        self.pr_number = pr_number
        self.comments: List[Comment] = []
        self.file_path = f"~/.pr-agent/pr-{pr_number}-comments.json"
    
    def add_comment(self, comment: Comment):
        self.comments.append(comment)
        self.save()
    
    def save(self):
        # Save to JSON
    
    def load(self):
        # Load from JSON
    
    def to_markdown(self) -> str:
        # Export as markdown for review
```

#### 2.2 Comment Extractor (`src/comment_extractor.py`)
**Purpose:** Parse LLM responses to extract structured comments

```python
import re
from typing import List

def extract_comments_from_response(text: str) -> List[Comment]:
    """
    Parse LLM response for comments in format:
    **File**: path/file.py
    **Line**: 42
    **Code**: original code
    **Comment**: suggestion
    """
    # Regex parsing logic
```

---

### **Phase 3: UI Components (1.5 hours)**

#### 3.1 Sidebar (`src/ui/sidebar.py`)
```python
import streamlit as st

def render_sidebar():
    with st.sidebar:
        st.title("🤖 PR Review Agent")
        
        # PR Selection
        pr_number = st.number_input("PR Number", min_value=1)
        
        if st.button("🔍 Analyze PR"):
            return {'action': 'analyze', 'pr_number': pr_number}
        
        # Settings
        with st.expander("⚙️ Settings"):
            model = st.selectbox("Model", ["gpt-4", "gpt-4o", "claude-sonnet-4.5"])
            
        return None
```

#### 3.2 Review Panel (`src/ui/review_panel.py`)
```python
import streamlit as st

def render_review_panel(summary, findings, comments, comment_store):
    st.markdown("### 📋 Review Summary")
    if summary:
        st.info(summary)
    
    st.markdown("### 🔍 Key Findings")
    if findings:
        for finding in findings:
            st.warning(finding)
    
    st.markdown("### 💬 Comments")
    st.caption(f"{len(comments)} comments")
    
    for i, comment in enumerate(comments):
        with st.expander(f"📝 {comment.file}:{comment.line}", expanded=(i==0)):
            severity_icon = {
                'issue': '🔴',
                'suggestion': '🟡', 
                'comment': '🔵'
            }[comment.severity]
            
            st.markdown(f"{severity_icon} **{comment.severity.title()}**")
            
            if comment.code_snippet:
                st.code(comment.code_snippet, language="python")
            
            st.markdown(comment.comment)
            
            # Edit/Delete buttons
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("✏️ Edit", key=f"edit_{i}"):
                    st.session_state[f'editing_{i}'] = True
            with col2:
                if st.button("🗑️ Delete", key=f"del_{i}"):
                    comment_store.remove(i)
                    st.rerun()
    
    st.divider()
    
    # Post to GitHub
    if comments:
        if st.button("📤 Post Comments to GitHub", type="primary", use_container_width=True):
            return {'action': 'post_comments'}
    
    return None
```

#### 3.3 Chat Panel (`src/ui/chat_panel.py`)
```python
import streamlit as st

def render_chat_panel(analyzer):
    st.markdown("### 💭 Chat with Agent")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about this PR..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = analyzer.chat(prompt)
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Extract any comments from response
        extracted = extract_comments_from_response(response)
        if extracted:
            st.session_state.comment_store.add_comments(extracted)
            st.rerun()
```

---

### **Phase 4: Main App (1 hour)**

#### 4.1 Create `streamlit_app.py`
```python
import streamlit as st
from src.analyzer import PRAnalyzer
from src.comment_store import CommentStore
from src.ui.sidebar import render_sidebar
from src.ui.review_panel import render_review_panel
from src.ui.chat_panel import render_chat_panel
from src.repo_utils import check_repo_clean, RepoError

# Page config
st.set_page_config(
    page_title="PR Review Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def init_session_state():
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = None
    if 'comment_store' not in st.session_state:
        st.session_state.comment_store = None
    if 'summary' not in st.session_state:
        st.session_state.summary = None
    if 'findings' not in st.session_state:
        st.session_state.findings = []

init_session_state()

# Sidebar
action = render_sidebar()

# Handle actions
if action and action['action'] == 'analyze':
    pr_number = action['pr_number']
    
    # Check repo is clean
    try:
        if not check_repo_clean():
            st.error("Repository has uncommitted changes. Please commit or stash.")
            st.stop()
    except RepoError as e:
        st.error(f"Not in a git repository: {e}")
        st.stop()
    
    # Initialize analyzer
    with st.spinner(f"Analyzing PR #{pr_number}..."):
        st.session_state.analyzer = PRAnalyzer(pr_number)
        st.session_state.comment_store = CommentStore(pr_number)
        
        # Run analysis (async)
        import asyncio
        analysis = asyncio.run(st.session_state.analyzer.analyze())
        
        # Parse analysis into summary/findings
        # ... parsing logic ...
        
        st.success("Analysis complete!")

# Main layout
if st.session_state.analyzer:
    # 2-column layout
    left, right = st.columns([1, 2])
    
    with left:
        action = render_review_panel(
            st.session_state.summary,
            st.session_state.findings,
            st.session_state.comment_store.comments,
            st.session_state.comment_store
        )
        
        if action and action['action'] == 'post_comments':
            # Post to GitHub
            with st.spinner("Posting comments..."):
                # gh CLI to post comments
                pass
            st.success("Comments posted!")
    
    with right:
        render_chat_panel(st.session_state.analyzer)

else:
    # Welcome screen
    st.title("🤖 PR Review Agent")
    st.info("👈 Enter a PR number in the sidebar to start")
    
    st.markdown("""
    ### Features
    - 📋 Comprehensive PR analysis with codebase context
    - 💬 Interactive chat to ask questions
    - 📝 Structured comments with file/line references
    - ✅ Review all comments before posting
    """)
```

#### 4.2 Update Launch Scripts

**Update `src/cli.py`:**
```python
@click.command()
@click.option('--port', default=8501, help='Port to run on')
def main(port):
    """Launch PR Review Agent."""
    import subprocess
    subprocess.run([
        "streamlit", "run", "streamlit_app.py",
        "--server.port", str(port)
    ])
```

---

### **Phase 5: Analyzer Integration (30 min)**

#### 5.1 Update `src/analyzer.py`
**Add method to parse analysis into structured data:**

```python
class PRAnalyzer:
    # ... existing code ...
    
    def parse_analysis(self, analysis_text: str) -> dict:
        """Parse analysis into structured data for UI.
        
        Returns:
            {
                'summary': str,
                'findings': List[str],
                'suggestions': List[str]
            }
        """
        # Parse markdown sections
        sections = {}
        current_section = None
        
        for line in analysis_text.split('\n'):
            if line.startswith('## Summary'):
                current_section = 'summary'
                sections['summary'] = []
            elif line.startswith('## Key Findings'):
                current_section = 'findings'
                sections['findings'] = []
            elif line.startswith('## Suggestions'):
                current_section = 'suggestions'
                sections['suggestions'] = []
            elif current_section and line.strip():
                sections[current_section].append(line)
        
        return {
            'summary': '\n'.join(sections.get('summary', [])),
            'findings': sections.get('findings', []),
            'suggestions': sections.get('suggestions', [])
        }
```

---

### **Phase 6: Testing & Refinement (30 min)**

#### 6.1 Test Checklist
- [ ] Launch app: `uv run streamlit run streamlit_app.py`
- [ ] Test PR selection and analysis
- [ ] Test 2-panel layout responsiveness
- [ ] Test chat interaction
- [ ] Test comment extraction
- [ ] Test comment editing/deletion
- [ ] Test posting to GitHub
- [ ] Test branch restore on session end

#### 6.2 Common Issues & Fixes
- **Asyncio in Streamlit:** Use `asyncio.run()` for async calls
- **State persistence:** Use `st.session_state` extensively
- **Rerun triggers:** Use `st.rerun()` after state changes
- **Layout breaks:** Test different screen sizes

---

## File Structure (After Migration)

```
agents/pr-review/
├── streamlit_app.py          # NEW: Main Streamlit app
├── app.py                     # DEPRECATED: Old Chainlit app
├── pyproject.toml             # UPDATE: Add streamlit
├── README.md                  # UPDATE: Change instructions
├── src/
│   ├── analyzer.py            # UPDATE: Add parse_analysis()
│   ├── comment_store.py       # NEW: Comment management
│   ├── comment_extractor.py   # NEW: Parse comments from LLM
│   ├── ui/                    # NEW: UI components
│   │   ├── __init__.py
│   │   ├── sidebar.py
│   │   ├── review_panel.py
│   │   └── chat_panel.py
│   ├── prompts.py             # KEEP: No changes
│   ├── prompt_loader.py       # KEEP: No changes
│   ├── repo_utils.py          # KEEP: No changes
│   ├── gh_utils.py            # KEEP: No changes
│   └── state.py               # KEEP: No changes
├── prompts/                   # KEEP: No changes
└── .streamlit/                # NEW: Streamlit config
    └── config.toml
```

---

## Launch Commands

### Old (Chainlit)
```bash
uv run chainlit run app.py --port 8000
```

### New (Streamlit)
```bash
uv run streamlit run streamlit_app.py --server.port 8501
```

Or via CLI:
```bash
uv run pr-agent --port 8501
```

---

## Rollback Plan

If migration doesn't work out:
1. Keep `app.py` (Chainlit version) in place
2. Streamlit version in `streamlit_app.py` 
3. Can switch between them easily
4. No backend code changed, so easy to revert

---

## Estimated Timeline

| Phase | Task | Time |
|-------|------|------|
| 1 | Setup dependencies & structure | 30 min |
| 2 | Core components (comment store/extractor) | 1 hour |
| 3 | UI components (sidebar/panels) | 1.5 hours |
| 4 | Main app integration | 1 hour |
| 5 | Analyzer integration | 30 min |
| 6 | Testing & refinement | 30 min |
| **Total** | | **~4.5 hours** |

*Note: Original estimate was 2-3 hours, revised to 4.5 hours for more thorough implementation*

---

## Success Criteria

✅ **Must Have:**
- [ ] 2-panel layout (summary left, chat right)
- [ ] Comments accumulate in left panel
- [ ] Can review all comments before posting
- [ ] Chat works same as before
- [ ] Backend logic unchanged (analyzer, prompts)

✅ **Nice to Have:**
- [ ] Edit/delete individual comments
- [ ] Export comments as markdown
- [ ] Responsive mobile layout
- [ ] Keyboard shortcuts

---

## Next Steps

1. **Review this plan** - Any changes needed?
2. **Start Phase 1** - Add dependencies, create structure
3. **Implement components** - Work through phases 2-6
4. **Test thoroughly** - Ensure feature parity
5. **Update documentation** - README, etc.
6. **Deprecate Chainlit** - Optional, can keep both

Ready to start implementation?
