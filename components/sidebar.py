"""
Sidebar Component with Real-time Model Fetching
"""

import streamlit as st
from typing import Dict
from utils.llm_handler import LLMHandler


def render_sidebar(llm_handler: LLMHandler) -> Dict:
    """Render the sidebar and return configuration"""
    
    config = {
        'template_file': None,
        'use_llm': False,
        'selected_model': 'llama-3.3-70b-versatile',
        'num_slides': 10,
        'include_real_time_data': False,
        'colors': {},
        'fonts': {},
        'layout_preferences': {}
    }
    
    with st.sidebar:
        # Header
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h1 style="
                background: linear-gradient(135deg, #6366F1 0%, #EC4899 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 1.8rem;
                font-weight: 800;
            ">🎯 AI Presentation</h1>
            <p style="color: #94A3B8; font-size: 0.9rem;">Enterprise Architect</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Template Upload
        st.markdown("### 📁 Template Upload")
        
        template_type = st.radio(
            "Upload Type",
            ["PowerPoint (.pptx)", "Image (PNG/JPEG)"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        if template_type == "PowerPoint (.pptx)":
            uploaded_file = st.file_uploader("Upload Template", type=['pptx'])
        else:
            uploaded_file = st.file_uploader("Upload Screenshot", type=['png', 'jpg', 'jpeg'])
        
        if uploaded_file:
            config['template_file'] = uploaded_file
            st.success(f"✓ {uploaded_file.name}")
        
        st.divider()
        
        # AI Configuration with Real-time Models
        st.markdown("### 🤖 AI Content Generation")
        
        config['use_llm'] = st.toggle("Enable AI Generation", value=True)
        
        if config['use_llm']:
            # Fetch and display real-time models
            with st.spinner("Loading available models..."):
                models_info = llm_handler.get_models_for_ui()
            
            if models_info:
                # Create model options
                model_ids = [m[0] for m in models_info]
                model_names = {m[0]: m[1] for m in models_info}
                model_descriptions = {m[0]: m[2] for m in models_info}
                recommended = [m[0] for m in models_info if m[3]]
                
                # Model selector
                selected = st.selectbox(
                    "Select AI Model",
                    options=model_ids,
                    format_func=lambda x: f"{'⭐ ' if x in recommended else ''}{model_names.get(x, x)}",
                    index=0
                )
                
                config['selected_model'] = selected
                
                # Show model info
                if selected in model_descriptions:
                    st.caption(f"ℹ️ {model_descriptions[selected]}")
                
                # Refresh models button
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("🔄", help="Refresh model list"):
                        llm_handler.fetch_available_models(force_refresh=True)
                        st.rerun()
            else:
                st.warning("Could not fetch models. Using default.")
                config['selected_model'] = 'llama-3.3-70b-versatile'
            
            # Real-time data toggle
            config['include_real_time_data'] = st.toggle(
                "Include Real-time Web Data",
                value=False,
                help="Search the web for current information"
            )
        
        st.divider()
        
        # Slide Configuration
        st.markdown("### 📊 Slide Configuration")
        
        config['num_slides'] = st.slider(
            "Number of Slides",
            min_value=1,
            max_value=50,
            value=10
        )
        
        with st.expander("🎨 Layout Preferences"):
            config['layout_preferences']['include_charts'] = st.checkbox("Include Charts", value=True)
            config['layout_preferences']['include_tables'] = st.checkbox("Include Tables", value=True)
            config['layout_preferences']['include_timeline'] = st.checkbox("Include Timeline", value=False)
            config['layout_preferences']['include_comparison'] = st.checkbox("Include Comparisons", value=False)
        
        st.divider()
        
        # Custom Styling
        st.markdown("### 🎨 Custom Styling")
        
        with st.expander("Colors"):
            col1, col2 = st.columns(2)
            with col1:
                config['colors']['primary'] = st.color_picker("Primary", value="#6366F1")
                config['colors']['background'] = st.color_picker("Background", value="#0F172A")
            with col2:
                config['colors']['accent'] = st.color_picker("Accent", value="#EC4899")
                config['colors']['text_primary'] = st.color_picker("Text", value="#F8FAFC")
        
        with st.expander("Typography"):
            config['fonts']['title_size'] = st.slider("Title Size", 24, 72, 44)
            config['fonts']['body_size'] = st.slider("Body Size", 10, 32, 18)
            config['fonts']['font_family'] = st.selectbox(
                "Font Family",
                ["Arial", "Helvetica", "Times New Roman", "Calibri", "Georgia"]
            )
        
        st.divider()
        
        # Export Options
        st.markdown("### 💾 Export Options")
        config['export_format'] = st.radio("Format", ["PowerPoint (.pptx)", "PDF"], horizontal=True)
        
        # Footer
        st.markdown("""
        <div style="text-align: center; padding: 1rem; margin-top: 2rem; border-top: 1px solid #334155;">
            <p style="color: #64748B; font-size: 0.75rem;">
                AI Presentation Architect v2.0<br>
                Powered by Groq
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    return config
