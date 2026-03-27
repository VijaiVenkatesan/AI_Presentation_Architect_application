"""
Sidebar Configuration Component
Fixed: API key hidden when in secrets, template override option
"""
import streamlit as st
from typing import Dict

def render_sidebar() -> Dict:
    result = {'generate': False, 'topic': '', 'num_slides': 10}
    
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Check if API key exists in secrets
        api_in_secrets = False
        try:
            if hasattr(st, 'secrets') and st.secrets.get("GROQ_API_KEY"):
                api_in_secrets = True
        except:
            pass
        
        # Only show API key input if NOT in secrets
        if not api_in_secrets:
            api_key = st.text_input(
                "🔑 Groq API Key",
                type="password",
                value=st.session_state.get('groq_api_key', ''),
                help="Get your API key from https://console.groq.com"
            )
            if api_key:
                st.session_state.groq_api_key = api_key
        else:
            st.success("✅ API Key configured in secrets")
        
        # Presentation settings
        st.subheader("📊 Presentation Settings")
        
        topic = st.text_input(
            "Presentation Topic",
            value=st.session_state.get('presentation_topic', ''),
            placeholder="e.g., Agentic AI 2026 Business Trends"
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
            st.success(f"✅ Template uploaded: {template_file.name}")
        
        # Template override option
        st.divider()
        if st.session_state.get('template_file'):
            st.session_state.use_template = st.checkbox(
                "Use uploaded template",
                value=st.session_state.get('use_template', True)
            )
            if not st.session_state.use_template:
                st.session_state.template_file = None
                st.info("📝 Will use default PowerPoint template")
        else:
            st.session_state.use_template = False
        
        # Generate button
        st.divider()
        
        if st.button(
            "🚀 Generate Presentation",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.get('generation_in_progress', False)
        ):
            if not topic:
                st.error("❌ Please enter a presentation topic")
            elif not api_in_secrets and not st.session_state.get('groq_api_key'):
                st.error("❌ Please enter your Groq API key")
            else:
                st.session_state.presentation_topic = topic
                st.session_state.num_slides = num_slides
                st.session_state.presentation_title = topic
                st.session_state.generation_in_progress = True
                
                result = {
                    'generate': True,
                    'topic': topic,
                    'num_slides': num_slides
                }
                
                st.success("✅ Starting generation...")
        
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
        
        if st.session_state.get('template_file') and st.session_state.get('use_template'):
            st.success("✅ Custom template active")
        
        # Quick actions
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save", use_container_width=True):
                from app import auto_save_presentation
                auto_save_presentation()
                st.success("✅ Saved!")
        
        with col2:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.slides = []
                st.session_state.presentation_title = ''
                st.session_state.presentation_topic = ''
                st.session_state.current_slide_index = 0
                st.session_state.template_file = None
                st.session_state.use_template = False
                st.rerun()
        
        # Help
        st.divider()
        with st.expander("❓ Help"):
            st.markdown("""
            ### Quick Start
            1. Enter your Groq API key (or set in secrets)
            2. Enter a presentation topic
            3. Choose number of slides (3-20)
            4. Optional: Upload a PPTX template
            5. Click "Generate Presentation"
            
            ### Tips
            - Be specific with your topic for better results
            - Use templates for consistent branding
            - Edit slides in the Editor tab
            - Export to PPTX or PDF when done
            """)
    
    return result
