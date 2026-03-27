"""Sidebar Component - API key hidden when in secrets"""
import streamlit as st
from typing import Dict

def render_sidebar() -> Dict:
    result = {'generate': False, 'topic': '', 'num_slides': 10}
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Check for API key in secrets
        api_in_secrets = False
        try:
            if hasattr(st, 'secrets') and st.secrets.get("GROQ_API_KEY"):
                api_in_secrets = True
        except: pass
        
        if not api_in_secrets:
            api_key = st.text_input("🔑 Groq API Key", type="password", value=st.session_state.get('groq_api_key',''), help="Get from https://console.groq.com")
            if api_key: st.session_state.groq_api_key = api_key
        else:
            st.success("✅ API configured in secrets")
        
        st.subheader("📊 Presentation")
        topic = st.text_input("Topic", value=st.session_state.get('presentation_topic',''), placeholder="e.g., Agentic AI 2026")
        num_slides = st.slider("Slides", 3, 20, st.session_state.get('num_slides', 10))
        
        template = st.file_uploader("📁 Template (optional)", type=['pptx'])
        if template: st.session_state.template_file = template
        
        st.divider()
        if st.button("🚀 Generate", type="primary", use_container_width=True):
            if not topic: st.error("❌ Enter a topic")
            elif not api_in_secrets and not st.session_state.get('groq_api_key'): st.error("❌ Enter API key")
            else:
                st.session_state.presentation_topic = topic
                st.session_state.num_slides = num_slides
                st.session_state.presentation_title = topic
                result = {'generate': True, 'topic': topic, 'num_slides': num_slides}
                st.success("✅ Starting...")
        
        st.divider()
        st.subheader("📈 Status")
        if st.session_state.get('slides'): st.success(f"✅ {len(st.session_state.slides)} slides")
        else: st.info("⏳ No slides yet")
        if st.session_state.get('api_configured'): st.success("✅ API Connected")
        else: st.warning("⚠️ API Not Configured")
        
        st.divider()
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.slides = []
            st.session_state.presentation_title = ''
            st.session_state.presentation_topic = ''
            st.rerun()
    
    return result
