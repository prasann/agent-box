"""Streamlit UI for PR Review Agent."""

import streamlit as st
import asyncio

from src.analyzer import PRAnalyzer, AnalyzerError
from src.comment_store import CommentStore
from src.ui import render_sidebar, render_review_panel, render_chat_panel
from src.repo_utils import check_repo_clean, RepoError
from src.gh_utils import get_pr_info, GhError


# Page configuration
st.set_page_config(
    page_title="PR Review Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """Initialize session state variables."""
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = None
    if 'comment_store' not in st.session_state:
        st.session_state.comment_store = None
    if 'summary' not in st.session_state:
        st.session_state.summary = None
    if 'findings' not in st.session_state:
        st.session_state.findings = []
    if 'pr_number' not in st.session_state:
        st.session_state.pr_number = None
    if 'pr_info' not in st.session_state:
        st.session_state.pr_info = None
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False


def parse_analysis(analysis_text: str) -> dict:
    """Parse analysis text into structured data.
    
    Args:
        analysis_text: Raw analysis from LLM
        
    Returns:
        Dictionary with summary and findings
    """
    sections = {
        'summary': [],
        'findings': [],
        'suggestions': []
    }
    
    current_section = None
    lines = analysis_text.split('\n')
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Detect section headers
        if line_lower.startswith('## summary') or line_lower.startswith('#summary'):
            current_section = 'summary'
            continue
        elif 'key finding' in line_lower or 'findings:' in line_lower:
            current_section = 'findings'
            continue
        elif 'suggestion' in line_lower or 'recommendation' in line_lower:
            current_section = 'suggestions'
            continue
        
        # Add content to current section
        if current_section and line.strip():
            # Skip markdown headers
            if not line.strip().startswith('#'):
                sections[current_section].append(line.strip())
    
    # Join summary into single string
    summary = '\n'.join(sections['summary']) if sections['summary'] else analysis_text[:500]
    
    # Combine findings and suggestions
    all_findings = sections['findings'] + sections['suggestions']
    
    return {
        'summary': summary,
        'findings': all_findings
    }


def handle_analyze(pr_number: int):
    """Handle PR analysis request.
    
    Args:
        pr_number: PR number to analyze
    """
    # Check repo is clean
    try:
        if not check_repo_clean():
            st.error("⚠️ **Repository has uncommitted changes**\n\n"
                    "Please commit or stash your changes before reviewing PRs.")
            return
    except RepoError as e:
        st.error(f"⚠️ **Not in a git repository**\n\n{e}")
        return
    
    # Fetch PR info first
    try:
        pr_info = get_pr_info(pr_number)
        st.session_state.pr_info = pr_info
    except GhError as e:
        st.error(f"❌ **Failed to fetch PR info:** {e}")
        return
    
    # Show progress
    with st.status(f"🔍 Analyzing PR #{pr_number}: {pr_info['title']}...", expanded=True) as status:
        st.write("Initializing analyzer...")
        
        # Initialize analyzer and comment store
        st.session_state.pr_number = pr_number
        st.session_state.analyzer = PRAnalyzer(pr_number)
        st.session_state.comment_store = CommentStore(pr_number)
        
        st.write("Running analysis with full codebase context...")
        
        try:
            # Run analysis (async)
            analysis = asyncio.run(st.session_state.analyzer.analyze())
            
            st.write("Parsing analysis results...")
            
            # Parse analysis into structured data
            parsed = parse_analysis(analysis)
            st.session_state.summary = parsed['summary']
            st.session_state.findings = parsed['findings']
            st.session_state.analysis_complete = True
            
            status.update(label="✅ Analysis complete!", state="complete")
            
        except AnalyzerError as e:
            status.update(label="❌ Analysis failed", state="error")
            st.error(f"**Analysis Error:** {e}")
        except Exception as e:
            status.update(label="❌ Unexpected error", state="error")
            st.error(f"**Unexpected Error:** {e}")


def handle_reset():
    """Reset the application state."""
    # Cleanup analyzer if exists
    if st.session_state.analyzer:
        try:
            asyncio.run(st.session_state.analyzer.cleanup())
        except Exception:
            pass  # Ignore cleanup errors
    
    # Clear all state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Reinitialize
    init_session_state()
    st.rerun()


def handle_post_comments():
    """Post comments to GitHub."""
    if not st.session_state.comment_store or not st.session_state.comment_store.comments:
        st.warning("No comments to post!")
        return
    
    pr_number = st.session_state.pr_number
    comments = st.session_state.comment_store.comments
    
    with st.spinner(f"Posting {len(comments)} comments to PR #{pr_number}..."):
        try:
            # TODO: Implement actual GitHub posting using gh CLI
            # For now, just show success message
            # Example implementation:
            # import subprocess
            # for comment in comments:
            #     body = f"**{comment.severity.title()}:** {comment.comment}"
            #     subprocess.run(['gh', 'pr', 'comment', str(pr_number), '--body', body], check=True)
            
            st.success(f"✅ Posted {len(comments)} comments to PR #{pr_number}!")
            st.info("💡 **Note:** Comment posting is not yet fully implemented. "
                   "Use 'Export MD' to get markdown format for manual posting.")
            
        except Exception as e:
            st.error(f"❌ Failed to post comments: {e}")


def handle_export_markdown():
    """Export comments as markdown."""
    if st.session_state.comment_store:
        markdown = st.session_state.comment_store.to_markdown()
        
        # Show download button
        st.download_button(
            label="📥 Download Markdown",
            data=markdown,
            file_name=f"pr-{st.session_state.pr_number}-comments.md",
            mime="text/markdown"
        )


def handle_delete_comment(index: int):
    """Delete a comment.
    
    Args:
        index: Comment index to delete
    """
    if st.session_state.comment_store:
        st.session_state.comment_store.remove_comment(index)
        st.success("Comment deleted!")
        st.rerun()


def handle_clear_comments():
    """Clear all comments."""
    if st.session_state.comment_store:
        st.session_state.comment_store.clear()
        st.success("All comments cleared!")
        st.rerun()


def render_welcome_screen():
    """Render welcome screen when no PR is being analyzed."""
    st.title("🤖 PR Review Agent")
    
    st.markdown("""
    Welcome to the **PR Review Agent**! This tool helps you perform comprehensive 
    code reviews with AI assistance.
    """)
    
    st.info("👈 **Get Started:** Enter a PR number in the sidebar and click 'Analyze'")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✨ Features")
        st.markdown("""
        - 📋 **Comprehensive Analysis** - Full codebase context
        - 💬 **Interactive Chat** - Ask questions about the PR
        - 📝 **Structured Comments** - File/line references
        - ✅ **Review Before Posting** - Edit/delete comments
        - 📤 **GitHub Integration** - Post directly to PR
        """)
    
    with col2:
        st.markdown("### 🚀 How It Works")
        st.markdown("""
        1. **Select PR** - Enter a PR number
        2. **Analyze** - AI reviews the full codebase
        3. **Chat** - Ask questions and refine
        4. **Review** - Check all comments
        5. **Post** - Submit to GitHub
        """)
    
    st.divider()
    
    st.markdown("### 📚 Tips")
    st.markdown("""
    - Ask specific questions about code patterns or design decisions
    - Request clarification on findings
    - Suggest alternative approaches
    - Use the chat to explore different aspects of the PR
    """)


def main():
    """Main application entry point."""
    # Initialize session state
    init_session_state()
    
    # Render sidebar (returns actions)
    action = render_sidebar()
    
    # Handle sidebar actions
    if action:
        if action['action'] == 'analyze':
            handle_analyze(action['pr_number'])
        elif action['action'] == 'reset':
            handle_reset()
    
    # Main content area
    if st.session_state.analyzer and st.session_state.analysis_complete:
        # Show PR info header
        if st.session_state.pr_info:
            pr = st.session_state.pr_info
            st.markdown(f"# PR #{st.session_state.pr_number}: {pr['title']}")
            author = pr['author']['login'] if isinstance(pr['author'], dict) else pr['author']
            base_ref = pr.get('baseRefName', 'main')
            head_ref = pr.get('headRefName', 'branch')
            st.caption(f"👤 {author} • {base_ref} ← {head_ref}")
            st.divider()
        
        # Create 2-column layout
        left_col, right_col = st.columns([1, 2])
        
        # Left panel: Review summary and comments
        with left_col:
            review_action = render_review_panel(
                st.session_state.summary,
                st.session_state.findings,
                st.session_state.comment_store.comments,
                st.session_state.comment_store
            )
            
            # Handle review panel actions
            if review_action:
                if review_action['action'] == 'post_comments':
                    handle_post_comments()
                elif review_action['action'] == 'export_markdown':
                    handle_export_markdown()
                elif review_action['action'] == 'delete_comment':
                    handle_delete_comment(review_action['index'])
                elif review_action['action'] == 'clear_comments':
                    handle_clear_comments()
        
        # Right panel: Chat interface
        with right_col:
            render_chat_panel(st.session_state.analyzer)
    
    else:
        # Show welcome screen
        render_welcome_screen()


if __name__ == "__main__":
    main()
