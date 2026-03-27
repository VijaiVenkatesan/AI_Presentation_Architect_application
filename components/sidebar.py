"""
Sidebar Configuration Component
"""
import streamlit as st
from typing import Dict, Optional

def render_sidebar() -> Dict:
    """Render the configuration sidebar"""
    
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key
        api_key = st.text_input(
            "🔑 Groq API Key",
            type="password",
            value=st.session_state.get('groq_api_key', ''),
            help="Get your API key from https://console.groq.com"
        )
        
        if api_key:
            st.session_state.groq_api_key = api_key
        
        # Presentation settings
        st.subheader("📊 Presentation Settings")
        
        topic = st.text_input(
            "Presentation Topic",
            value=st.session_state.get('presentation_topic', ''),
            placeholder="e.g., Agentic AI 2025 Business Trends"
        )
        
        num_slides = st.slider(
            "Number of Slides",
            min_value=3,
            max_value=100,
            value=st.session_state.get('num_slides', 10)
        )
        
        # Template upload
        template_file = st.file_uploader(
            "📁 Upload Template (Optional)",
            type=['pptx'],
            help="Upload a PowerPoint template to use"
        )
        
        if template_file:
            st.session_state.template_file = template_file
        
        # Generate button
        st.divider()
        
        if st.button("🚀 Generate Presentation", type="primary", use_container_width=True):
            if not topic:
                st.error("Please enter a presentation topic")
            elif not st.session_state.get('groq_api_key'):
                st.error("Please enter your Groq API key")
            else:
                st.session_state.presentation_topic = topic
                st.session_state.num_slides = num_slides
                st.session_state.presentation_title = topic
                return {
                    'generate': True,
                    'topic': topic,
                    'num_slides': num_slides,
                    'api_key': api_key
                }
        
        # Status
        st.divider()
        st.subheader("📈 Status")
        
        if st.session_state.get('slides', []):
            st.success(f"✅ {len(st.session_state.slides)} slides generated")
        else:
            st.info("⏳ No slides yet")
        
        if st.session_state.get('api_configured', False):
            st.success("✅ API Connected")
        else:
            st.warning("⚠️ API Not Configured")
        
        # Quick actions
        st.divider()
        
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.slides = []
            st.session_state.presentation_title = ''
            st.session_state.presentation_topic = ''
            st.session_state.current_slide_index = 0
            st.rerun()
    
    return {}
