"""Chat panel component for interactive conversation."""

import streamlit as st
import asyncio
from ..analyzer import PRAnalyzer
from ..comment_extractor import auto_extract_comments


def render_chat_panel(analyzer: PRAnalyzer | None):
    """Render chat panel with message history and input.
    
    Args:
        analyzer: PR analyzer instance
    """
    st.markdown("## 💭 Chat with Agent")
    
    if not analyzer:
        st.info("👈 Start by analyzing a PR to chat with the agent")
        return
    
    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about this PR...", key="chat_input"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Add to analyzer state
        analyzer.state.add_message("user", prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Call analyzer's chat method
                    # Use get_event_loop to avoid "Event loop is closed" error
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    response = loop.run_until_complete(analyzer._chat(analyzer.state.get_conversation()))
                    
                    # Display response
                    st.markdown(response)
                    
                    # Add to chat history and analyzer state
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    analyzer.state.add_message("assistant", response)
                    
                    # Extract any comments from response
                    extracted = auto_extract_comments(response)
                    if extracted:
                        st.session_state.comment_store.add_comments(extracted)
                        st.success(f"✅ Extracted {len(extracted)} comment(s) from response")
                        # Trigger rerun to update review panel
                        st.rerun()
                    
                except Exception as e:
                    error_msg = f"❌ **Error:** {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    # Suggested prompts (only show when chat is empty)
    if len(st.session_state.messages) == 0:
        st.markdown("### 💡 Suggested Questions")
        
        suggestions = [
            "What are the main changes in this PR?",
            "Are there any potential bugs or issues?",
            "Can you suggest improvements for code quality?",
            "Are there any security concerns?",
            "Is the code well-tested?",
        ]
        
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                    # Simulate user input
                    st.session_state.pending_prompt = suggestion
                    st.rerun()


def handle_pending_prompt():
    """Handle pending prompt from suggestion buttons.
    
    This is a workaround for button clicks in suggestions.
    """
    if 'pending_prompt' in st.session_state:
        prompt = st.session_state.pending_prompt
        del st.session_state.pending_prompt
        return prompt
    return None
