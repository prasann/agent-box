# Agentic PR Review Agent - Simple Architecture

> **Goal**: Use Copilot SDK to automatically analyze PRs and generate review comments, then refine them through natural conversation.

---

## 🎯 Simple Workflow

```
User: pr-agent review 123

Agent automatically:
  1. Fetches PR diff (via gh CLI)
  2. Analyzes all changes (via Copilot SDK)
  3. Generates review comments
  4. Stores in state file
  5. Ready for conversation

User: "show me the comments"
Agent: [Lists all comments with IDs]

User: "make comment 3 more concise"
Agent: [Updates comment 3, shows new version]

User: "skip comment 5"
Agent: [Removes comment 5]

User: "post the review"
Agent: [Posts to GitHub via gh CLI]
```

**No complex tools. No commands. Just natural conversation + LLM intelligence.**

---

## 🧠 Core Approach: LLM-Driven Everything

### 1. **One Analysis Call**
Send entire PR diff to Copilot SDK with a detailed prompt:
- "Analyze this PR and generate structured review comments"
- Prompt defines comment format, severity levels, what to look for
- LLM returns JSON with all comments

### 2. **Conversational Refinement**
User asks to modify comments in natural language:
- "make this more concise"
- "skip the style comments"
- "focus only on bugs"
- LLM understands intent and updates the state

### 3. **State Management**
Simple JSON file stores:
```json
{
  "pr_number": 123,
  "comments": [
    {
      "id": 1,
      "file": "src/auth.ts",
      "line": 45,
      "severity": "critical",
      "comment": "SQL injection vulnerability",
      "status": "active"
    }
  ]
}
```

### 4. **Prompt Configuration**
Review style configured via prompts in code:
- Comment structure
- Severity definitions
- What to check for (security, performance, etc.)
- Tone and format

---

## 🏗️ Proposed Agentic Architecture

### Core Agent with Tool Ecosystem

```
┌─────────────────────────────────────────────────────────────┐
│                    PR Review Agent (Main)                    │
│  - Natural conversation interface                           │
│  - Intent detection & planning                              │
│  - Context management                                       │
│  - Multi-agent orchestration                                │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│  Custom Tools    │    │   MCP Servers    │
├──────────────────┤    ├──────────────────┤
│ • analyze_file   │    │ • GitHub MCP     │
│ • add_feedback   │    │ • Filesystem MCP │
│ • search_code    │    │ • Git MCP        │
│ • read_context   │    │ • Test Runner    │
│ • suggest_fix    │    │ • Dependency     │
│ • run_tests      │    │   Analyzer       │
└──────────────────┘    └──────────────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
         ┌────────────────────────┐
         │  Specialized Agents    │
         ├────────────────────────┤
         │ • Security Agent       │
    � Example Conversation Flow

### Initial Review  │
         └────────────────────────┘
```
$ pr-agent review 123

Agent: 🔍 Analyzing PR #123: "Add user authentication"

[Automatically fetches diff, analyzes with Copilot SDK]

✓ Analysis complete. Found 5 review comments:

1. [CRITICAL] src/auth.ts:45 - SQL injection vulnerability
2. [IMPORTANT] src/api.ts:120 - Missing error handling
3. [SUGGESTION] src/controller.ts:89 - Can use optional chaining
4. [SUGGESTION] src/utils.ts:23 - Consider extracting to constant
5. [QUESTION] tests/auth.test.ts:67 - Should test edge case?

How would you like to proceed?
```

### Refining Comments

```
You: show me comment 1

Agent: Comment 1 - CRITICAL

File: src/auth.ts, Line 45
Issue: SQL injection vulnerability

The query uses string interpolation which allows SQL injection:
```
const query = `SELECT * FROM users WHERE id = ${userId}`;
```

Suggested fix:
```
const query = 'SELECT * FROM users WHERE id = ?';
const result = await db.query(query, [userId]);
```

---

You: make this comment more concise

Agent: ✓ Updated comment 1:

File: src/auth.ts:45 - SQL injection risk from string interpolation.
Use parameterized queries instead.

---

You: skip comment 3 and 4

Agent: ✓ Removed comments 3 and 4. 
Now have 3 active comments.

---

You: post the review

Agent: 📤 Posting review with REQUEST_CHANGES action...
✓ Posted to PR #123
View at: https://github.com/owner/repo/pull/123         file_path: { type: "string" }
        },
        required: ["file_path"]
    },
    handler: async ({ file_path }) => {
        const diff = await execCommand(`gh pr diff --name-only | grep ${file_path} && gh pr diff`);
        return { file: file_path, diff };
    }
});
```

---

## 🔧 Tool Implementation with gh CLI

### Example: Complete Tool Handler

```python
import subprocess
import json
from typing import Any, Dict

async def exec_command(command: str) -> str:
    """Execute shell command and return output."""
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()

# Tool definition using Copilot SDK
analyze_file_tool = {
    "name": "analyze_file",
    "description": "Deep analysis of a specific file in the PR with git history",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to analyze"
            }
        },
        "required": ["file_path"]
    },
    "handler": async def analyze_file(file_path: str) -> Dict[str, Any]:
        # Read current content
        content = Path(file_path).read_text()
        
        # Get git history
        history = await exec_command(
            f"git log --oneline -n 5 -- {file_path}"
        )
        
        # Get git blame
        blame = await exec_command(f"git blame {file_path}")
        
        # Check if file has tests
        test_path = file_path.replace("src/", "tests/").replace(".py", "_test.py")
        has_tests = Path(test_path).exists()
        
        return {
            "file": file_path,
            "content": content,
            "lines": len(content.split("\n")),
            "history": history.split("\n"),
            "has_tests": has_tests,
            "test_path": test_path if has_tests else None
        }
}
```

---

## 🎬 User Experience: Agentic Flows

### Flow 1: Natural Language Review

```
User: "Let's review PR 123"

Agent: 
  → Fetches PR data
  → Analyzes diff automatically
  → Identifies patterns
  
  "I've analyzed PR #123: 'Add user authentication'.
   
   I found several areas worth discussing:
   
   1. Security: The password hashing in auth.ts looks good
   2. ⚠️ Concern: No rate limiting on the login endpoint
   3. 💡 Tests: Missing tests for token expiration
   
   Would you like me to:
   - Do a deep security review?
   - Check for similar patterns in the codebase?
   - Create feedback items for these concerns?"

User: "Yes, do the security review"

Agent:
  → Invokes security agent
  → Uses detectSecurityIssues tool
  → Searches for related vulnerabilities
  → Generates structured feedback
  
  "Security review complete. Found 3 issues:
   
   🔴 Critical: SQL injection risk in user lookup (auth.ts:45)
   🟡 Important: Missing CSRF tokens on auth endpoints
   💡 Suggestion: Consider adding brute-force protection
   
   I've added these as review feedback. 
   Would you like me to suggest fixes?"
```

### Flow 2: Conversational Feedback

```
User: "The error handling in the controller looks wrong"

Agent:
  → Understands "error handling" + "controller" 
  → Uses searchCodebase to find controller files
  → Uses analyzeFile on relevant controllers
  
  "I found 3 controllers in the PR. Which one?
   - UserController.ts (lines 120-180)
   - AuthController.ts (lines 45-67)
   - OrderController.ts (lines 234-256)"

User: "The AuthController"

Agent:
  → Analyzes AuthController.ts:45-67
  → Identifies error handling patterns
  
  "Looking at AuthController.ts:45-67, I see:
   - Errors are caught but not logged
   - Generic 500 status for all failures
   - No retry logic for transient failures
   
   Is this what you're concerned about?"

User: "Yes, add that as feedback"

Agent:
  → Invokes addFeedback tool
  → Automatically determines severity
  → Suggests fix
  
  "✓ Added feedback:
   
   File: AuthController.ts:45-67
   Severity: Important
   Issue: Inadequate error handling - errors not logged,
          generic status codes, no retry logic
   
   Suggested fix: [generates code showing proper error handling]
   
   Added to review draft. Want me to check other controllers?"
```

### Flow 3: Proactive Analysis

```
User: "Review this PR"

Agent:
  → Initial analysis
  → Detects database changes
  → Proactively checks for migration issues
  
  "I notice this PR modifies the database schema.
   Let me check a few things...
   
   🔍 Checking for:
   - Migration scripts ✓ Found
   - Backwards compatibility ⚠️ Issue detected
   - Index performance ✓ Good
   
   Important: The migration drops a column without a 
   rollback plan. This could break the current deployment.
   
   Should I:
   1. Add this as critical feedback?
   2. Search for other migration patterns?
   3. Review the entire migration strategy?"

User: "1"

Agent:Autonomous Analysis & Review

```
User: "Review PR 123 and post feedback"

Agent:
  → Uses getPRDetails tool
  → Analyzes all changed files
  → Uses checkTests tool
  → Identifies issues
  
  "Starting review of PR #123...
   
   🔍 Analyzing 5 changed files...
   ├─ auth.ts: Security concern detected
   ├─ api.ts: No test coverage found
   ├─ controller.ts: Performance issue in loop
   └─ utils.ts: Looks good ✓
   
   📊 Found 3 issues:
   
   1. 🔴 auth.ts:45 - Potential SQL injection
   2. 🟡 api.ts - Missing tests for new endpoints
   3. 💡 controller.ts:89 - Inefficient array iteration
   
   I've drafted feedback for these. Review?"

User: "Show me the auth.ts issue"

Agent:
  → Uses analyzeFile tool
  → Uses suggestFix tool
  
  "Looking at auth.ts:45-52:
   
   Current code:
   ```
   const query = `SELECT * FROM users WHERE id = ${userId}`;
   const result = await db.query(query);
   ```
   
   Issue: Direct string interpolation allows SQL injection.
   
   Suggested fix:
   ```
   const query = 'SELECT * FROM users WHERE id = ?';
   const result = await db.query(query, [userId]);
   ```
   
   Want me to add this suggestion to the review?"

User: "Yes, aCore SDK Integration (1 week)
- [ ] Replace current CopilotClient wrapper with proper SDK usage
- [ ] Set up session with `createSession()` and proper config
- [ ] Add streaming support with event handlers
- [ ] Implement 3 basic tools: `analyze_file`, `add_feedback`, `search_codebase`

### Phase 2: Tool Ecosystem (1-2 weeks)
- [ ] Implement remaining core tools (8-10 total)
- [ ] Add gh CLI wrappers for GitHub operations
- [ ] Create tool handler utilities for command execution
- [ ] Add error handling and validation

### Phase 3: Natural Language Interface (1 week)
- [ ] Remove all slash commands from REPL
- [ ] Let SDK handle tool selection via natural language
- [ ] Implement conversational feedback loop
- [ ] Add clarification questions when needed

### Phase 4: Intelligent Analysis (1-2 weeks)
- [ ] Add automatic PR analysis on start
- [ ] Implement proactive issue detection
- [ ] Create fix suggestion system
- [ ] Add test coverage checking

### Phase 5: Polish & Refinement (ongoing)
- [ ] Improve tool descriptions for better intent matching
- [ ] Add progress indicators during tool execution
- [ ] Enhance system prompts for better reasoning
- [ ] Optimize context managementeeks)
- [ ] Implement core tool definitions
- [ ] Set up MCP server connections (GitHub, Filesystem, Git)
- [ ] Create tool handler framework
- [ ] Add streaming responses for progress updates

### Phase 2: Intent Detection (1-2 weeks)
- [ ] Build natural language → tool mapping
- [ ] Implement conversational context tracking
- [ ] Add clarification question system
- [ ] Remove slash commands entirely

### Phase 3: Specialized Agents (2-3 weeks)
- [ ] Implement security agent
- [ ] Implement performance agent
- [ ] Implement test coverage agent
- [ ] Add agent orchestration system

### Phase 4: Proactive Analysis (2 weeks)
- [ ] Automatic PR categorization (security-relevant, perf-critical, etc.)
- [ ] Heuristic-based issue detection
- [ ] Pattern matching against known issues
- [ ] Proactive context gathering

### Phase 5: Polish & Intelligence (ongoing)
- [ ] Improve intent understanding
- [ ] Add learning from feedback patterns
- [ ] Enhance fix generation
- [ ] Multi-turn reasoning improvements

---

## 📊 Comparison: Before & After

| Aspect | Current (Command-Based) | Proposed (Agentic) |
|--------|------------------------|-------------------|
| **Interaction** | `/feedback file:45 "bug"` | "This could cause issues" |
| **Context** | User provides everything | Agent gathers dynamically |
| **Analysis** | User-initiated queries | Proactive scanning |
| **Feedback** | Manual command entry | Natural conversation → structured data |
| **Intelligence** | Q&A only | Intent understanding + actions |
| **Multi-tasking** | Sequential commands | Agent can use multiple tools |
| **Fix Suggestions** | None | Automated code generation |
| **Progress Visibility** | Silent execution | Streaming with tool call indicators |

---

## 💡 Key Benefits

### For Reviewers
- **Natural conversation** instead of command syntax
- **Proactive insights** without explicit queries
- **Intelligent assis: Minimal Implementation

### Step 1: Update SDK Client Setup

```python
# src/pr_agent/agent_client/client.py
from copilot import CopilotClient, defineTool

clasBetter fix suggestions** with code generation

### For Development Workflow
- **Faster reviews** with tool automation
- **Lower barrier** - no commands to learn
- **Better context** - agent fetches what it needs
- **Iterative improvement** - agent learns from conversation
        # Define all tools
        self.tools = [
            self._create_analyze_file_tool(),
            self._create_add_feedback_tool(),
            self._create_search_codebase_tool(),
        ]
    
    def _create_analyze_file_tool(self):
        async def handler(file_path: str):
            # Implementation here
            pass
        
        return defineTool("analyze_file", {
            "description": "Analyze a specific file in the PR with context",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"}
                },
                "required": ["file_path"]
            },
            "handler": handler
        })
    
    async def start_review(self):
        """Initialize the agentic review session."""
        await self.client.start()
        
        # Create session with tools
        self.session = await self.client.create_session({
            "model": "gpt-4.1",
            "streaming": True,
            "system_message": {
                "content": f"""You are an expert code reviewer for PR #{self.pr_number}.
                
You have these capabilities:
- Analyze specific files with context (git history, tests, etc.)
- Add structured review feedback
- Search the codebase for patterns

Important:
- Understand user intent from natural language
- Ask clarifying questions when needed
- Be proactive in identifying issues
- Suggest concrete fixes when appropriate
                """
            },
            "tools": self.tools
        })
        
        return self.session
```

### Step 2: Update REPL for Natural Language

```python
# src/pr_agent/chat/repl.py
class AgenticChatREPL:
    async def _handle_user_input(self, user_input: str):
        """Process any user input - no command parsing needed."""
        
        # Add to conversation
        self.session.add_message("user", user_input)
        
        # Stream response
        conuses tools autonomously** - Decides when to analyze, search, etc.
3. **Understands context** - Gathers information as needed via tools
4. **Conversational feedback** - "This looks wrong" → Structured comment
5. **Streaming responses** - See agent thinking in real-time
6. **gh CLI integration** - Uses existing tooling effectively
        def on_message_delta(event):
            if event.type == "assistant.message_delta":
                content = event.data.delta_content
                if content:
                    process.stdout.write(content)
                    response_parts.append(content)
        
        def on_tool_call(event):
            if event.type == "tool.call":
                tool_name = event.data.tool_name
                console.print(f"\n[dim]→ Using tool: {tool_name}[/dim]")
        
        self.copilot_session.on("assistant.message_delta", on_message_delta)
        self.copilot_session.on("tool.call", on_tool_call)
        
        # Send and wait
        await self.copilot_session.send_and_wait({"prompt": user_input})
        
        # Save conversation
        full_response = "".join(response_parts)
        self.session.add_message("assistant", full_response)
        self.session.save()
```

### Step 3: Remove All Command Parsing

```python
# In repl.py - simplified main loop
async def _run_loop(self):
    while True:
        try:
            user_input = await asyncio.to_thread(
                self.prompt_session.prompt,
                f"pr-{self.session.pr_number}> "
            )
            
            user_input = user_input.strip()
            if not user_input:
                continue
            
            # Check for exit
            if user_input.lower() in ["exit", "quit"]:
                break
            
            # Everything goes to the agent - no command parsing!
            await self._handle_user_input(user_input)
            
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
```

This immediately gives you:
- ✅ Natural language: "analyze the auth file" instead of `/analyze auth.ts`
- ✅ Tool calling: Agent decides when to use tools
- ✅ Conversational: "add that as feedback" works naturally
- ✅ Streaming: See agent's thinking in real-time
- ✅ No command syntax to learn
    // Agent decides what to do based on conversation
    const response = await session.sendAndWait({ prompt: userInput });
    
    console.log("Agent:", response.data.content);
}
```

This immediately enables:
- Natural language instead of `/feedback` commands
- Agent can search codebase autonomously
- Agent can add feedback from conversation
- No need to learn command syntax

Then gradually add:
- More tools (security scans, test checks, etc.)
- MCP servers (GitHub, filesystem access)
- Specialized agents
- Proactive analysis

---

## 📚 Technical References

- [Copilot SDK - Getting Started](https://github.com/github/copilot-sdk/blob/main/docs/getting-started.md)
- [Tool Definition Guide](https://github.com/github/copilot-sdk/blob/main/docs/getting-started.md#step-4-add-a-custom-tool)
- [MCP Integration](https://github.com/github/copilot-sdk/blob/main/docs/mcp.md)
- [Custom Agents](https://github.com/github/copilot-sdk/blob/main/docs/getting-started.md#create-custom-agents)

---

## ✅ Success Criteria

The agentic agent is successful when:

1. **No slash commands needed** - Everything through natural language
2. **Agent takes initiative** - Proactively finds issues
3. **Understands context** - Gathers information autonomously
4. **Multi-agent coordination** - Different experts working together
5. **Conversational feedback** - "This looks wrong" → Structured comment
6. **Learning system** - Gets better with each review

---

## 🎯 Next Steps

### Week 1: Core SDK Integration
1. Update `agent_client/client.py` to use `defineTool()` properly
2. Implement 3 core tools: `analyze_file`, `add_feedback`, `search_codebase`
3. Update REPL to remove command parsing
4. Add streaming with event handlers

### Week 2: Expand Tool Ecosystem  
1. Add 5 more tools (gh CLI wrappers, git operations)
2. Test natural language → tool calling flow
3. Improve system prompts for better tool usage
4. Add progress indicators

### Week 3: Polish & Test
1. Test with real PRs
2. Improve tool descriptions based on usage
3. Add error handling
4. Document the agentic approach

The goal is to make PR review feel like **pair programming with an expert colleague** who can autonomously explore the codebase and provide insightful feedback through natural conversation.
