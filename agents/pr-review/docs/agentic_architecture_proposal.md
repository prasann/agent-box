# Agentic PR Review Agent - Architecture Proposal

> **Goal**: Transform the current command-based CLI into an intelligent, autonomous agent that can proactively analyze PRs, gather context dynamically, and assist with reviews through natural conversation and autonomous actions.

---

## 🎯 Vision: From Command Tool → Intelligent Agent

### Current State (Command-Based)
```
User types: /feedback file.ts:45 critical "bug here"
         ↓
    Direct command execution
         ↓
    Feedback stored
```

### Proposed State (Agentic)
```
User says: "This looks like it could cause a race condition"
         ↓
    Agent understands intent
         ↓
    Agent identifies relevant code
         ↓
    Agent asks clarifying questions
         ↓
    Agent creates structured feedback
         ↓
    Agent suggests fixes proactively
```

---

## 🧠 Key Agentic Capabilities from Copilot SDK

### 1. **Tool Calling** (defineTool)
The agent can define and invoke functions autonomously based on conversation context.

**What This Enables:**
- Natural language → Actions
- Dynamic context gathering
- Autonomous code analysis
- Proactive suggestions

### 2. **MCP Server Integration**
Connect to Model Context Protocol servers for extended capabilities.

**Available MCP Servers:**
- **GitHub MCP** - Direct PR operations, issue tracking
- **Filesystem MCP** - Read codebase beyond changed files
- **Git MCP** - Advanced git operations, history analysis
- **Custom MCP** - Project-specific analyzers (tests, dependencies, etc.)

### 3. **Custom Agents**
Define specialized AI personas for different review aspects.

**Examples:**
- Security reviewer
- Performance analyzer  
- Test coverage checker
- Documentation reviewer

### 4. **Streaming & Events**
Real-time agent thinking and progress updates.

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
         │ • Performance Agent    │
         │ • Test Coverage Agent  │
         │ • Style/Docs Agent     │
         └────────────────────────┘
```

---

## 🛠️ Tool Definitions

### 1. Context Exploration Tools

```typescript
const analyzeFile = defineTool("analyze_file", {
    description: "Deep analysis of a specific file in the PR",
    parameters: {
        type: "object",
        properties: {
            file_path: { type: "string" },
            focus_areas: { 
                type: "array",
                items: { enum: ["security", "performance", "logic", "tests"] }
            }
        },
        required: ["file_path"]
    },
    handler: async ({ file_path, focus_areas }) => {
        // Read file content, git history, related files
        // Run static analysis
        // Return structured insights
    }
});

const searchCodebase = defineTool("search_codebase", {
    description: "Search for similar patterns or related code in the repository",
    parameters: {
        type: "object",
        properties: {
            query: { type: "string" },
            file_type: { type: "string" },
            include_tests: { type: "boolean" }
        },
        required: ["query"]
    },
    handler: async ({ query, file_type, include_tests }) => {
        // Use grep/ripgrep for fast search
        // Return relevant code snippets with context
    }
});

const getRelatedContext = defineTool("get_related_context", {
    description: "Get context related to changed code (imports, usages, tests)",
    parameters: {
        type: "object",
        properties: {
            file_path: { type: "string" },
            symbol: { type: "string" },
            context_type: { 
                enum: ["imports", "usages", "tests", "dependencies"] 
            }
        },
        required: ["file_path", "symbol"]
    },
    handler: async ({ file_path, symbol, context_type }) => {
        // Find all usages, imports, tests
        // Use LSP or static analysis
    }
});
```

### 2. Review Action Tools

```typescript
const addFeedback = defineTool("add_feedback", {
    description: "Add structured review feedback for specific code",
    parameters: {
        type: "object",
        properties: {
            file: { type: "string" },
            lines: { type: "string" },
            severity: { enum: ["critical", "important", "suggestion", "question"] },
            comment: { type: "string" },
            suggested_fix: { type: "string" }
        },
        required: ["file", "comment", "severity"]
    },
    handler: async (args) => {
        session.feedback.add_item(args);
        return { success: true, id: item.id };
    }
});

const suggestCodeFix = defineTool("suggest_code_fix", {
    description: "Generate a concrete code fix for an identified issue",
    parameters: {
        type: "object",
        properties: {
            file: { type: "string" },
            issue_description: { type: "string" },
            current_code: { type: "string" }
        },
        required: ["file", "issue_description"]
    },
    handler: async ({ file, issue_description, current_code }) => {
        // Generate suggested diff
        // Validate syntax
        // Return formatted suggestion
    }
});

const checkTests = defineTool("check_tests", {
    description: "Check if changed code has adequate test coverage",
    parameters: {
        type: "object",
        properties: {
            file: { type: "string" },
            functions: { type: "array", items: { type: "string" } }
        },
        required: ["file"]
    },
    handler: async ({ file, functions }) => {
        // Find related test files
        // Check coverage
        // Identify missing tests
    }
});
```

### 3. GitHub Integration Tools (using gh CLI)

```typescript
const postReviewComment = defineTool("post_review_comment", {
    description: "Post a review comment to the GitHub PR",
    parameters: {
        type: "object",
        properties: {
            pr_number: { type: "number" },
            action: { enum: ["comment", "approve", "request-changes"] },
            body: { type: "string" }
        },
        required: ["pr_number", "action", "body"]
    },
    handler: async ({ pr_number, action, body }) => {
        // Use gh CLI to post review
        const result = await execCommand(
            `gh pr review ${pr_number} --${action} --body "${body}"`
        );
        return { success: true, url: `PR #${pr_number}` };
    }
});

const getPRDetails = defineTool("get_pr_details", {
    description: "Get detailed information about a PR including files, commits, and status",
    parameters: {
        type: "object",
        properties: {
            pr_number: { type: "number" }
        },
        required: ["pr_number"]
    },
    handler: async ({ pr_number }) => {
        const prJson = await execCommand(`gh pr view ${pr_number} --json title,body,files,commits`);
        return JSON.parse(prJson);
    }
});

const getFileDiff = defineTool("get_file_diff", {
    description: "Get the diff for a specific file in the PR",
    parameters: {
        type: "object",
        properties: {
            file_path: { type: "string" }
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
