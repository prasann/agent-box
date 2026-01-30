# PR Review Agent - Implementation Plan

## Development Philosophy

**Keep It Simple:**
- Standard Python libraries wherever possible
- No Docker, no complex installers
- Use `uv` for fast, modern Python packaging
- Local development, local installation
- Iterate quickly, validate with real PRs

---

## Technology Stack

### Core Technologies
- **Python**: 3.13+ (using modern features)
- **Package Manager**: `uv` (fast, modern alternative to pip/poetry)
- **GitHub Copilot SDK**: For AI reasoning (need to verify Python client availability)
- **CLI Framework**: `click` (standard, simple)
- **Interactive REPL**: `prompt_toolkit` (rich terminal experience)
- **Terminal UI**: `rich` (beautiful formatting)
- **Data Models**: `pydantic` (validation and serialization)

### Standard Library Usage
- `subprocess` - Run `gh` and `git` commands
- `json` - Session state persistence
- `pathlib` - File operations
- `os` / `shutil` - Directory management
- `typing` - Type hints

### External Tools (Already on macOS)
- `gh` CLI - GitHub API access (must be authenticated)
- `git` - Repository context

---

## Project Setup

### Directory Structure
```
agents/pr-review/
├── README.md
├── docs/
│   ├── mvp_spec.md
│   ├── approach.md
│   └── implementation_plan.md (this file)
├── pyproject.toml           # uv project config
├── src/
│   └── pr_agent/
│       ├── __init__.py
│       ├── cli.py           # Entry point
│       ├── chat/            # Interactive chat
│       ├── agent/           # Core logic
│       ├── context/         # Context gathering
│       ├── copilot/         # Copilot SDK wrapper
│       ├── state/           # Session management
│       └── models/          # Data models
├── tests/
│   └── ...
├── scripts/
│   ├── install.sh           # Simple install script
│   └── dev-setup.sh         # Dev environment setup
└── examples/
    └── sample_review.md
```

### Installation Approach (Simple!)
```bash
# 1. Install dependencies with uv
cd agents/pr-review
uv sync

# 2. Install CLI in development mode
uv pip install -e .

# 3. Verify
pr-agent --help
```

---

## Phase 1: Foundation (Week 1)

**Goal**: Basic working chat interface that can fetch a PR and respond to simple questions.

### Tasks

#### 1.1 Project Scaffolding (Day 1)
- [ ] Create `pyproject.toml` with uv configuration
- [ ] Set up basic package structure (`src/pr_agent/`)
- [ ] Create entry point (`cli.py`) with click
- [ ] Add `scripts/install.sh` for local installation
- [ ] Verify `pr-agent` command works

**Tech Details:**
```toml
# pyproject.toml (uv format)
[project]
name = "pr-agent"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "click>=8.1.0",
    "prompt-toolkit>=3.0.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
]

[project.scripts]
pr-agent = "pr_agent.cli:main"
```

#### 1.2 Basic CLI Commands (Day 1-2)
- [ ] Implement `pr-agent review <number>` command skeleton
- [ ] Detect current git repo (use `git rev-parse`)
- [ ] Basic error handling (not in a repo, no PR number)
- [ ] Print welcome message

**Tech Approach:**
```python
# Use subprocess for git
import subprocess
from pathlib import Path

def get_repo_info():
    repo_root = subprocess.run(
        ['git', 'rev-parse', '--show-toplevel'],
        capture_output=True, text=True
    ).stdout.strip()
    
    remote = subprocess.run(
        ['git', 'config', '--get', 'remote.origin.url'],
        capture_output=True, text=True
    ).stdout.strip()
    
    # Parse owner/repo from remote URL
    return parse_github_url(remote)
```

#### 1.3 PR Fetching (Day 2-3)
- [ ] Create `context/pr_fetcher.py`
- [ ] Fetch PR metadata via `gh pr view <number> --json`
- [ ] Fetch PR diff via `gh pr diff <number>`
- [ ] Parse JSON response into Pydantic models
- [ ] Cache to session directory

**Tech Approach:**
```python
# Use gh CLI (already authenticated)
import subprocess
import json

def fetch_pr_data(pr_number: int) -> dict:
    result = subprocess.run(
        ['gh', 'pr', 'view', str(pr_number), '--json',
         'title,body,author,files,commits,number'],
        capture_output=True, text=True
    )
    return json.loads(result.stdout)

def fetch_pr_diff(pr_number: int) -> str:
    result = subprocess.run(
        ['gh', 'pr', 'diff', str(pr_number)],
        capture_output=True, text=True
    )
    return result.stdout
```

#### 1.4 Session Management (Day 3)
- [ ] Create `state/session.py` and `state/storage.py`
- [ ] Implement session directory creation (`~/.config/pr-agent/sessions/`)
- [ ] Save PR metadata and diff to session files
- [ ] Load existing sessions

**Tech Approach:**
```python
# Use pathlib for paths
from pathlib import Path
import json

class SessionManager:
    def __init__(self):
        self.base_path = Path.home() / '.config' / 'pr-agent' / 'sessions'
    
    def create_session(self, owner, repo, pr_number):
        session_dir = self.base_path / owner / repo / f'pr-{pr_number}'
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
    
    def save_metadata(self, session_dir, data):
        with open(session_dir / 'metadata.json', 'w') as f:
            json.dump(data, f, indent=2)
```

#### 1.5 Copilot SDK Integration (Day 4-5)
- [ ] Install GitHub Copilot SDK: `uv add github-copilot-sdk`
- [ ] Review SDK docs: https://github.com/github/copilot-sdk
- [ ] Create `copilot/client.py` wrapper
- [ ] Implement authentication (via GitHub token from gh CLI)
- [ ] Test basic chat completion

**Tech Approach:**
```python
# GitHub Copilot SDK (confirmed available)
# Install: pip install github-copilot-sdk
from github_copilot_sdk import CopilotClient

# Get token from gh CLI
def get_github_token():
    result = subprocess.run(
        ['gh', 'auth', 'token'],
        capture_output=True, text=True
    )
    return result.stdout.strip()

# Initialize client
client = CopilotClient(token=get_github_token())

# Chat completion
response = client.chat(messages=[
    {"role": "system", "content": "You are a code reviewer."},
    {"role": "user", "content": "What are the main changes?"}
])

# Streaming responses
for chunk in client.chat_stream(messages=[...]):
    print(chunk.content, end='', flush=True)
```

**Note**: Check SDK documentation for exact API and authentication methods.

#### 1.6 Basic Chat REPL (Day 5-6)
- [ ] Create `chat/repl.py` with prompt_toolkit
- [ ] Implement basic input loop
- [ ] Parse commands (text vs `/command`)
- [ ] Exit handling (`exit`, `/exit`)
- [ ] Use rich for formatted output

**Tech Approach:**
```python
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from rich.console import Console

class ChatREPL:
    def __init__(self, pr_number):
        self.session = PromptSession(
            history=FileHistory('.pr-agent-history')
        )
        self.console = Console()
        self.pr_number = pr_number
    
    def run(self):
        while True:
            try:
                user_input = self.session.prompt(f'pr-{self.pr_number}> ')
                if user_input in ['exit', 'quit']:
                    break
                if user_input.startswith('/'):
                    self.handle_command(user_input)
                else:
                    self.handle_question(user_input)
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
```

#### 1.7 Simple Q&A Flow (Day 6-7)
- [ ] Send user question + PR context to Copilot
- [ ] Stream response to terminal
- [ ] Save conversation to `conversation.json`
- [ ] Handle errors gracefully

**Phase 1 Deliverable:**
```bash
$ cd ~/my-repo
$ pr-agent review 123

🔍 Fetching PR #123...
✓ Loaded 8 files changed

━━━━━━━━━━━━━━━━━━━━━━━
PR #123: Add new feature
By: @author | 8 files
━━━━━━━━━━━━━━━━━━━━━━━

pr-123> what are the main changes?

[AI responds with analysis...]

pr-123> exit
✓ Session saved
```

---

## Phase 2: Context Enhancement (Week 2)

**Goal**: Smart context gathering from git and filesystem.

### Tasks

#### 2.1 File Reader (Day 1)
- [ ] Create `context/repo_reader.py`
- [ ] Read changed files from disk
- [ ] Handle missing/renamed files
- [ ] Limit file size (skip large files)

**Tech Approach:**
```python
from pathlib import Path

class RepoReader:
    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)
    
    def read_file(self, relative_path: str) -> str:
        file_path = self.repo_root / relative_path
        if file_path.exists() and file_path.stat().st_size < 1_000_000:  # 1MB limit
            return file_path.read_text()
        return None
```

#### 2.2 Git Context (Day 2-3)
- [ ] Create `context/git_context.py`
- [ ] Implement git log for files
- [ ] Implement git blame
- [ ] Get recent commits

**Tech Approach:**
```python
def get_file_history(file_path: str, limit: int = 10) -> list[str]:
    result = subprocess.run(
        ['git', 'log', '--oneline', f'-{limit}', '--', file_path],
        capture_output=True, text=True
    )
    return result.stdout.strip().split('\n')

def get_blame(file_path: str) -> str:
    result = subprocess.run(
        ['git', 'blame', file_path],
        capture_output=True, text=True
    )
    return result.stdout
```

#### 2.3 Smart Context Builder (Day 4-5)
- [ ] Create `context/context_builder.py`
- [ ] Implement context selection logic
- [ ] Handle small vs large PRs differently
- [ ] Build structured context for Copilot

**Tech Approach:**
```python
class ContextBuilder:
    def build_context(self, pr_data, changed_files):
        if len(changed_files) < 10:
            # Small PR: full context
            return self.build_full_context(pr_data, changed_files)
        else:
            # Large PR: chunked context
            return self.build_chunked_context(pr_data, changed_files)
    
    def build_full_context(self, pr_data, changed_files):
        return {
            'pr_metadata': pr_data,
            'diff': self.diff,
            'files': {f: self.read_file(f) for f in changed_files},
            'git_history': {f: self.get_history(f) for f in changed_files}
        }
```

#### 2.4 Improved Prompts (Day 6-7)
- [ ] Create `agent/prompts.py` with templates
- [ ] System prompt with reviewer guidelines
- [ ] Context injection formatting
- [ ] Task-specific prompts (analyze vs Q&A)

**Phase 2 Deliverable:**
Responses include relevant context from git history and related files.

---

## Phase 3: Feedback & Commands (Week 3)

**Goal**: Full chat commands and review feedback management.

### Tasks

#### 3.1 Command Parser (Day 1)
- [ ] Create `chat/commands.py`
- [ ] Parse `/feedback`, `/generate`, `/preview`, `/post`
- [ ] Validation and help text

#### 3.2 Feedback Management (Day 2-3)
- [ ] Implement `/feedback add` logic
- [ ] Parse file:lines syntax
- [ ] Save to `feedback.json`
- [ ] List/delete feedback items

**Tech Approach:**
```python
# feedback.json structure
{
    "items": [
        {
            "id": 1,
            "file": "src/auth.ts",
            "lines": "45-60",
            "comment": "Need null check here",
            "severity": "suggestion",
            "timestamp": "2026-01-30T10:30:00Z"
        }
    ]
}
```

#### 3.3 Conversation Persistence (Day 3-4)
- [ ] Save full chat history to `conversation.json`
- [ ] Load on resume
- [ ] Maintain conversation context

#### 3.4 Resume Session (Day 4-5)
- [ ] Implement `pr-agent resume <number>`
- [ ] Load existing session
- [ ] Restore conversation state
- [ ] Continue chat

#### 3.5 Status & Help Commands (Day 5-7)
- [ ] Implement `/status` - show session info
- [ ] Implement `/context` - show loaded context
- [ ] Implement `/help` - command reference
- [ ] Rich formatting for all outputs

**Phase 3 Deliverable:**
Full interactive workflow with feedback accumulation.

---

## Phase 4: Review Generation & Posting (Week 4) ✅

**Goal**: Generate and post reviews to GitHub.

### Tasks

#### 4.1 Review Generator (Day 1-3) ✅
- [x] Create `agent/review_generator.py`
- [x] Synthesize feedback into review comments
- [x] Use Copilot to improve wording (ReviewImprover class)
- [x] Format for GitHub (markdown)

#### 4.2 Preview Command (Day 3-4) ✅
- [x] Implement `/preview`
- [x] Show formatted review draft
- [x] Allow editing (open in $EDITOR via `/edit`)

#### 4.3 Post to GitHub (Day 4-5) ✅
- [x] Implement `/post` command
- [x] Use `gh pr review` to post
- [x] Support approve/request-changes/comment
- [x] Confirmation prompt
- [x] Auto-suggest action based on severity

**Tech Approach:**
```bash
# Using gh CLI
gh pr review 123 \
  --request-changes \
  --body "Review comments here"
```

#### 4.4 Testing & Polish (Day 6-7) ⚠️
- [x] Error handling
- [x] User feedback improvements
- [ ] Test with real PRs (manual testing needed)

**Phase 4 Deliverable:**
Complete end-to-end workflow from review to posting. ✅
- Review generator with smart decision logic
- Preview with formatted output
- Editor integration for review editing
- GitHub posting with confirmations
- Comprehensive error handling

**Phase 4 Documentation:**
See [Phase 4 Testing Guide](phase4_testing_guide.md) for testing instructions.

---

## Phase 5: Polish & Future (Week 5+)

**Goal**: Production ready, extensible foundation.

### Tasks

#### 5.1 Error Handling
- [ ] Comprehensive error messages
- [ ] Retry logic for API calls
- [ ] Graceful degradation

#### 5.2 Configuration
- [ ] Config file support (`~/.config/pr-agent/config.json`)
- [ ] Custom prompts
- [ ] Default settings

#### 5.3 Logging & Debugging
- [ ] Optional debug logging
- [ ] Session logs for troubleshooting

#### 5.4 Shared Utilities
- [ ] Extract reusable patterns to `shared/` module
- [ ] Copilot client wrapper
- [ ] State management
- [ ] CLI patterns

#### 5.5 Documentation
- [ ] Usage guide
- [ ] Architecture docs
- [ ] Contributing guide

#### 5.6 Command Mode (Optional)
- [ ] One-off commands for scripting
- [ ] `pr-agent ask 123 "question"`
- [ ] `pr-agent generate 123`

---

## Development Workflow

### Daily Development
```bash
# Start development
cd agents/pr-review

# Activate environment (uv handles this)
uv run pr-agent review 123

# Run tests
uv run pytest

# Format code
uv run ruff check src/
```

### Testing Strategy

**Manual Testing:**
- Use real PRs from your repositories
- Test with various PR sizes (small, medium, large)
- Test error cases (invalid PR, network issues)

**Unit Tests (Minimal):**
- Test core logic (context builder, parsers)
- Mock subprocess calls
- Test data models

**Integration Tests:**
- End-to-end with fixtures
- Test against sample PRs

---

## Dependencies Management

### Using uv

```bash
# Install uv (if not already)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize project
cd agents/pr-review
uv init

# Add dependencies
uv add click prompt-toolkit rich pydantic

# Install in dev mode
uv pip install -e .

# Update dependencies
uv lock
```

### Key Dependencies
```toml
[project]
dependencies = [
    "click>=8.1.0",             # CLI framework
    "prompt-toolkit>=3.0.0",    # Interactive REPL
    "rich>=13.0.0",             # Terminal formatting
    "pydantic>=2.0.0",          # Data validation
    "github-copilot-sdk",       # GitHub Copilot AI
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "ruff>=0.1.0",             # Linter/formatter
    "mypy>=1.0.0",             # Type checking
]
```

---

## Success Metrics

### Phase 1
- [ ] Can fetch and display PR info
- [ ] Chat interface works
- [ ] Can ask basic questions and get responses

### Phase 2
- [ ] Responses include git context
- [ ] Smart context selection works
- [ ] Handles large PRs gracefully

### Phase 3
- [ ] Can accumulate feedback
- [ ] Session resume works
- [ ] All chat commands functional

### Phase 4
- [x] Can generate review
- [x] Can post to GitHub
- [x] Smart decision suggestion based on severity
- [x] Review preview and editing
- [ ] End-to-end workflow tested with real PRs

### Phase 5
- [ ] Production ready
- [ ] Good error messages
- [ ] Foundation for more agents

---

## Risks & Mitigations

### Risk 1: Context Too Large for Copilot
**Impact**: Medium  
**Mitigation**: Implement smart chunking, token counting, prioritize important context

### Risk 2: gh CLI Rate Limits
**Impact**: Low  
**Mitigation**: Cache aggressively, handle rate limit errors gracefully

### Risk 3: Copilot SDK API Changes
**Impact**: Low  
**Mitigation**: Pin SDK version, keep wrapper isolated for easy updates

---

## Next Steps

1. **Immediate**: ✅ GitHub Copilot SDK confirmed available - `pip install github-copilot-sdk`
2. **Day 1**: Start Phase 1.1 - Project scaffolding with uv
3. **Week 1**: Complete Phase 1 foundation
4. **Week 2+**: Iterate through phases

---

**Philosophy**: Ship Phase 1 quickly, validate with real usage, then iterate. Don't over-engineer early.