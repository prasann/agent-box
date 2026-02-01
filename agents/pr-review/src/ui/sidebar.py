"""Sidebar component for PR selection and configuration."""

import streamlit as st


def render_sidebar():
    """Render sidebar with PR selection and settings.
    
    Returns:
        Dictionary with action and parameters, or None
    """
    with st.sidebar:
        st.title("🤖 PR Review Agent")
        
        # PR Selection
        st.markdown("### 📋 Pull Request")
        pr_number = st.number_input(
            "PR Number",
            min_value=1,
            value=st.session_state.get('pr_number', 1),
            help="Enter the PR number to analyze"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Analyze", type="primary", use_container_width=True):
                return {'action': 'analyze', 'pr_number': pr_number}
        
        with col2:
            if st.button("🔄 Reset", use_container_width=True):
                return {'action': 'reset'}
        
        st.divider()
        
        # Settings
        with st.expander("⚙️ Settings", expanded=False):
            model = st.selectbox(
                "Model",
                ["gpt-4", "gpt-4o", "claude-sonnet-4.5"],
                index=0,
                help="Select the AI model to use"
            )
            st.session_state['model'] = model
            
            max_context = st.slider(
                "Max Context Lines",
                min_value=50,
                max_value=500,
                value=200,
                step=50,
                help="Maximum lines of code context to include"
            )
            st.session_state['max_context'] = max_context
        
        # Help
        with st.expander("ℹ️ Help", expanded=False):
            st.markdown("""
            **How to use:**
            1. Enter a PR number
            2. Click "Analyze" to start review
            3. Review comments in left panel
            4. Chat with agent in right panel
            5. Post comments to GitHub when ready
            
            **Tips:**
            - Ask specific questions about the code
            - Request clarification on findings
            - Suggest alternative approaches
            """)
        
        st.divider()
        
        # Status
        if 'pr_number' in st.session_state and st.session_state.get('analyzer'):
            st.markdown("### 📊 Status")
            st.success(f"✅ Analyzing PR #{st.session_state['pr_number']}")
            
            if 'comment_store' in st.session_state:
                num_comments = len(st.session_state['comment_store'].comments)
                st.metric("Comments", num_comments)
        else:
            st.info("👈 Enter a PR number to start")
    
    return None
