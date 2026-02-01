"""Chainlit UI for PR Review Agent."""

import chainlit as cl
from src.analyzer import PRAnalyzer, AnalyzerError
from src.state import ReviewState
from src.gh_utils import get_pr_info, GhError
from src.repo_utils import check_repo_clean, RepoError


@cl.on_chat_start
async def start():
    """Initialize chat session."""
    # Check repo is clean before starting
    try:
        if not check_repo_clean():
            await cl.Message(
                content="⚠️ **Repository has uncommitted changes**\n\n"
                        "Please commit or stash your changes before reviewing PRs.\n\n"
                        "Run `git status` to see uncommitted changes."
            ).send()
            return
    except Exception as e:
        await cl.Message(
            content=f"⚠️ **Not in a git repository**\n\n"
                    f"Please run this agent from within a git repository.\n\n"
                    f"Error: {e}"
        ).send()
        return
    
    # Get PR number from user
    pr_number_input = await cl.AskUserMessage(
        content="Which PR number would you like to review?",
        timeout=60
    ).send()
    
    if not pr_number_input:
        await cl.Message(content="❌ No PR number provided. Please refresh and try again.").send()
        return
    
    try:
        pr_number = int(pr_number_input['output'])
    except ValueError:
        await cl.Message(content="❌ Invalid PR number. Please provide a valid number.").send()
        return
    
    # Store in session
    cl.user_session.set("pr_number", pr_number)
    
    # Initialize analyzer
    analyzer = PRAnalyzer(pr_number)
    cl.user_session.set("analyzer", analyzer)
    
    # Show loading message
    msg = cl.Message(content="")
    await msg.send()
    
    # Perform initial analysis
    try:
        # Fetch PR info first to show metadata
        pr_info = get_pr_info(pr_number)
        
        # Show simple loader
        msg.content = f"🔍 Analyzing **PR #{pr_number}: {pr_info['title']}**..."
        await msg.update()
        
        # Run analysis (this will build conversation internally)
        analysis = await analyzer.analyze()
        
        # Update with analysis
        msg.content = analysis
        await msg.update()
        
        await cl.Message(
            content="✅ Analysis complete! Ask me anything about this PR.",
            author="system"
        ).send()
        
    except RepoError as e:
        msg.content = f"❌ **Repository Error:** {e}\n\n" \
                      "Make sure you're in a git repository with no uncommitted changes."
        await msg.update()
    except (GhError, AnalyzerError) as e:
        msg.content = f"❌ **Error:** {e}\n\nYou can still ask questions, but I don't have the PR context."
        await msg.update()
    except Exception as e:
        msg.content = f"❌ **Unexpected error:** {e}"
        await msg.update()


@cl.on_message
async def message(msg: cl.Message):
    """Handle user messages."""
    analyzer = cl.user_session.get("analyzer")
    pr_number = cl.user_session.get("pr_number")
    
    if not analyzer:
        await cl.Message(content="❌ Session not initialized. Please refresh and start again.").send()
        return
    
    # Add user message to state
    analyzer.state.add_message("user", msg.content)
    
    # Create response message
    response_msg = cl.Message(content="")
    await response_msg.send()
    
    try:
        # Get AI response
        response = await analyzer._chat(analyzer.state.get_conversation())
        
        # Save assistant response
        analyzer.state.add_message("assistant", response)
        
        # Update message with response
        response_msg.content = response
        await response_msg.update()
        
    except Exception as e:
        response_msg.content = f"❌ **Error:** {e}"
        await response_msg.update()


@cl.on_chat_end
async def end():
    """Cleanup on session end."""
    analyzer = cl.user_session.get("analyzer")
    if analyzer:
        await analyzer.cleanup()
