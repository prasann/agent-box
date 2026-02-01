"""Review panel component for displaying summary and comments."""

import streamlit as st
from ..comment_store import Comment, CommentStore


def render_review_panel(summary: str | None, findings: list[str], comments: list[Comment], comment_store: CommentStore):
    """Render review panel with summary, findings, and comments.
    
    Args:
        summary: Review summary text
        findings: List of key findings
        comments: List of review comments
        comment_store: Comment store for persistence
        
    Returns:
        Dictionary with action, or None
    """
    st.markdown("## 📋 Review Summary")
    
    # Summary Section
    if summary:
        with st.container():
            st.markdown(summary)
    else:
        st.info("No analysis yet. Enter a PR number and click Analyze.")
        return None
    
    st.divider()
    
    # Key Findings Section
    if findings:
        st.markdown("### 🔍 Key Findings")
        for finding in findings:
            # Clean up finding text
            clean_finding = finding.strip('- ').strip()
            if clean_finding:
                st.warning(f"• {clean_finding}")
        st.divider()
    
    # Comments Section
    st.markdown(f"### 💬 Comments ({len(comments)})")
    
    if not comments:
        st.info("No comments yet. Chat with the agent to generate comments.")
        return None
    
    # Toolbar
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.caption(f"{len(comments)} comment{'s' if len(comments) != 1 else ''} ready to post")
    with col2:
        if st.button("📥 Export MD", use_container_width=True):
            return {'action': 'export_markdown'}
    with col3:
        if st.button("🗑️ Clear All", use_container_width=True):
            return {'action': 'clear_comments'}
    
    st.markdown("")
    
    # Display each comment
    for i, comment in enumerate(comments):
        severity_config = {
            'issue': {'icon': '🔴', 'color': '#ff4444'},
            'suggestion': {'icon': '🟡', 'color': '#ffbb33'},
            'comment': {'icon': '🔵', 'color': '#33b5e5'}
        }
        config = severity_config.get(comment.severity, {'icon': '💬', 'color': '#999999'})
        
        with st.expander(
            f"{config['icon']} `{comment.file}:{comment.line}` - {comment.severity.title()}",
            expanded=(i < 3)  # Expand first 3 comments
        ):
            # Severity badge
            st.markdown(
                f"<span style='background-color: {config['color']}; color: white; "
                f"padding: 2px 8px; border-radius: 3px; font-size: 12px; font-weight: bold;'>"
                f"{comment.severity.upper()}</span>",
                unsafe_allow_html=True
            )
            st.markdown("")
            
            # Code snippet
            if comment.code_snippet:
                st.markdown("**Code:**")
                # Detect language from file extension
                lang = "python" if comment.file.endswith('.py') else "text"
                st.code(comment.code_snippet, language=lang)
            
            # Comment text
            st.markdown("**Comment:**")
            st.markdown(comment.comment)
            
            st.markdown("")
            
            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("✏️ Edit", key=f"edit_{i}", use_container_width=True):
                    st.session_state[f'editing_{i}'] = True
                    return {'action': 'edit_comment', 'index': i}
            with col2:
                if st.button("🗑️ Delete", key=f"del_{i}", use_container_width=True):
                    return {'action': 'delete_comment', 'index': i}
    
    st.divider()
    
    # Post to GitHub button
    if comments:
        st.markdown("### 📤 Post to GitHub")
        st.caption("Review all comments above before posting")
        
        if st.button(
            "📤 Post All Comments to GitHub",
            type="primary",
            use_container_width=True,
            disabled=len(comments) == 0
        ):
            return {'action': 'post_comments'}
    
    return None


def render_comment_editor(comment: Comment, index: int):
    """Render comment editor form.
    
    Args:
        comment: Comment to edit
        index: Comment index
        
    Returns:
        Updated comment or None if cancelled
    """
    with st.form(f"edit_comment_form_{index}"):
        st.markdown("### ✏️ Edit Comment")
        
        file = st.text_input("File", value=comment.file)
        line = st.number_input("Line", value=comment.line, min_value=1)
        severity = st.selectbox(
            "Severity",
            ["issue", "suggestion", "comment"],
            index=["issue", "suggestion", "comment"].index(comment.severity)
        )
        code_snippet = st.text_area("Code Snippet", value=comment.code_snippet, height=100)
        comment_text = st.text_area("Comment", value=comment.comment, height=150)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save", use_container_width=True):
                return Comment(
                    file=file,
                    line=line,
                    code_snippet=code_snippet,
                    comment=comment_text,
                    severity=severity
                )
        with col2:
            if st.form_submit_button("❌ Cancel", use_container_width=True):
                return None
    
    return None
