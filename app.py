"""
AI Presentation Architect - Main Application
Enterprise-level PowerPoint generator with AI content creation
"""

import streamlit as st
import io
from datetime import datetime

# Import utilities
from utils.llm_handler import LLMHandler
from utils.template_analyzer import TemplateAnalyzer
from utils.ppt_generator import PresentationGenerator
from utils.search_handler import SearchHandler
from utils.preview_handler import PreviewHandler

# Import components
from components.sidebar import render_sidebar
from components.editor import render_editor
from components.preview import render_preview
from components.chat_interface import render_chat_interface


# Page configuration
st.set_page_config(
    page_title="AI Presentation Architect",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #F8FAFC !important;
    }
    
    /* Cards */
    .stCard {
        background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid #334155;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #1E293B;
        padding: 0.5rem;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #94A3B8;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        color: white;
    }
    
    /* Info boxes */
    .stAlert {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: #1E293B;
        border-radius: 8px;
    }
    
    /* Success message */
    .success-box {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Model badge */
    .model-badge {
        display: inline-block;
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 0.25rem;
    }
    
    /* Divider */
    hr {
        border-color: #334155;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    defaults = {
        'content': None,
        'template_data': None,
        'generated': False,
        'chat_history': [],
        'current_slide': 0
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main():
    """Main application"""
    
    initialize_session_state()
    
    # Initialize handlers
    llm_handler = LLMHandler()
    template_analyzer = TemplateAnalyzer()
    search_handler = SearchHandler()
    
    # Render sidebar and get configuration
    config = render_sidebar(llm_handler)
    
    # Main content area
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h1 style="
            background: linear-gradient(135deg, #6366F1 0%, #EC4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5rem;
            font-weight: 800;
        ">🎯 AI Presentation Architect</h1>
        <p style="color: #94A3B8; font-size: 1.1rem;">
            Create stunning enterprise presentations with AI-powered content generation
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Status indicators
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if llm_handler.is_configured():
            st.success("✓ AI Ready")
        else:
            st.warning("⚠ Add API Key")
    
    with col2:
        if config.get('template_file'):
            st.success("✓ Template Loaded")
        else:
            st.info("○ No Template")
    
    with col3:
        st.info(f"📊 {config.get('num_slides', 10)} Slides")
    
    with col4:
        if config.get('selected_model'):
            model_short = config['selected_model'].split('-')[0].title()
            st.info(f"🤖 {model_short}")
    
    st.divider()
    
    # Analyze template if uploaded
    if config.get('template_file') and not st.session_state.template_data:
        with st.spinner("Analyzing template..."):
            file_bytes = io.BytesIO(config['template_file'].read())
            config['template_file'].seek(0)
            
            if config['template_file'].name.endswith('.pptx'):
                st.session_state.template_data = template_analyzer.analyze_pptx(file_bytes)
            else:
                st.session_state.template_data = template_analyzer.analyze_image(file_bytes)
            
            st.success("Template analyzed successfully!")
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Generate", "✏️ Edit", "👁️ Preview", "💾 Export"])
    
    with tab1:
        st.markdown("### Create Your Presentation")
        
        # Chat interface for content input
        user_prompt = render_chat_interface(
            llm_handler,
            config.get('selected_model', 'llama-3.3-70b-versatile')
        )
        
        if user_prompt:
            with st.spinner("🚀 Generating presentation content..."):
                # Fetch real-time data if enabled
                real_time_data = None
                if config.get('include_real_time_data'):
                    with st.status("Searching for real-time data..."):
                        real_time_data = search_handler.compile_research_data(user_prompt)
                        st.write("✓ Data compiled")
                
                # Get template context
                template_context = st.session_state.template_data or template_analyzer._get_default_template()
                
                # Apply custom colors if set
                if config.get('colors'):
                    template_context['colors'].update(config['colors'])
                
                # Generate content
                content = llm_handler.generate_presentation_content(
                    prompt=user_prompt,
                    model=config.get('selected_model', 'llama-3.3-70b-versatile'),
                    num_slides=config.get('num_slides', 10),
                    template_context=template_context,
                    real_time_data=real_time_data,
                    layout_preferences=config.get('layout_preferences', {})
                )
                
                st.session_state.content = content
                st.session_state.generated = True
                
                # Add to chat history
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': f"Created presentation '{content.get('title', 'Untitled')}' with {len(content.get('slides', []))} slides."
                })
            
            st.success(f"✓ Generated {len(content.get('slides', []))} slides!")
            st.rerun()
        
        # Show current content summary
        if st.session_state.content:
            content = st.session_state.content
            
            st.markdown("---")
            st.markdown("### 📋 Current Presentation")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Title", content.get('title', 'Untitled')[:30] + "...")
            with col2:
                st.metric("Slides", len(content.get('slides', [])))
            with col3:
                st.metric("Status", "Ready" if st.session_state.generated else "Draft")
            
            # Slide overview
            with st.expander("📊 Slide Overview", expanded=False):
                for slide in content.get('slides', []):
                    layout_emoji = {
                        'title': '🎯', 'content': '📝', 'two_column': '📊',
                        'chart': '📈', 'table': '📋', 'quote': '💬',
                        'timeline': '⏰', 'comparison': '⚖️', 'conclusion': '🎬',
                        'metrics': '📊', 'image': '🖼️'
                    }
                    emoji = layout_emoji.get(slide.get('layout', 'content'), '📄')
                    st.markdown(f"{emoji} **Slide {slide.get('slide_number', '?')}**: {slide.get('title', 'Untitled')}")
    
    with tab2:
        if st.session_state.content:
            st.session_state.content = render_editor(st.session_state.content)
        else:
            st.info("Generate content first to edit slides")
    
    with tab3:
        if st.session_state.content:
            template_data = st.session_state.template_data or template_analyzer._get_default_template()
            
            # Apply custom settings
            if config.get('colors'):
                template_data['colors'].update(config['colors'])
            
            render_preview(st.session_state.content, template_data)
        else:
            st.info("Generate content first to see preview")
    
    with tab4:
    st.markdown("### 💾 Export Your Presentation")
    
    if st.session_state.content:
        content = st.session_state.content
        
        # Import PDF generator
        from utils.pdf_generator import PDFGenerator
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 PowerPoint Export")
            st.markdown("Download as .pptx file")
            
            if st.button("📥 Generate PowerPoint", use_container_width=True):
                with st.spinner("Creating PowerPoint..."):
                    template_data = st.session_state.template_data or template_analyzer._get_default_template()
                    
                    # Apply custom settings
                    custom_settings = {}
                    if config.get('colors'):
                        custom_settings['colors'] = config['colors']
                    if config.get('fonts'):
                        custom_settings['fonts'] = {
                            'title_size': config['fonts'].get('title_size', 44),
                            'body_size': config['fonts'].get('body_size', 18),
                            'font_family': config['fonts'].get('font_family', 'Arial')
                        }
                    
                    generator = PresentationGenerator(template_data)
                    pptx_file = generator.generate_presentation(content, custom_settings)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"presentation_{timestamp}.pptx"
                    
                    st.download_button(
                        label="⬇️ Download PPTX",
                        data=pptx_file,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        use_container_width=True
                    )
                    
                    st.success("✓ PowerPoint ready!")
        
        with col2:
            st.markdown("#### 📄 PDF Export")
            st.markdown("Download as .pdf file")
            
            if st.button("📥 Generate PDF", use_container_width=True):
                with st.spinner("Creating PDF..."):
                    template_data = st.session_state.template_data or template_analyzer._get_default_template()
                    
                    pdf_generator = PDFGenerator(template_data)
                    pdf_file = pdf_generator.generate_pdf(content)
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"presentation_{timestamp}.pdf"
                    
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=pdf_file,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                    st.success("✓ PDF ready!")
        
        st.divider()
        
        # Template info
        if st.session_state.template_data:
            with st.expander("📋 Template Information", expanded=False):
                td = st.session_state.template_data
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**Colors**")
                    for name, color in td.get('colors', {}).items():
                        st.markdown(
                            f'<div style="display:flex;align-items:center;gap:8px;">'
                            f'<div style="width:20px;height:20px;background:{color};border-radius:4px;border:1px solid #ccc;"></div>'
                            f'<span>{name}</span></div>',
                            unsafe_allow_html=True
                        )
                
                with col2:
                    st.markdown("**Fonts**")
                    for name, font in td.get('fonts', {}).items():
                        st.markdown(f"- {name}: {font.get('name', 'Arial')} {font.get('size', 18)}pt")
                
                with col3:
                    st.markdown("**Other**")
                    st.markdown(f"- Logo: {'✓' if td.get('has_logo') else '✗'}")
                    st.markdown(f"- Background: {td.get('background', {}).get('type', 'solid')}")
                    st.markdown(f"- Slide Size: {td.get('slide_size', {}).get('width', 13.33):.1f}\" × {td.get('slide_size', {}).get('height', 7.5):.1f}\"")
        
        st.divider()
        
        # Export summary
        st.markdown("### 📊 Export Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Slides", len(content.get('slides', [])))
        with col2:
            charts = sum(1 for s in content.get('slides', []) if s.get('layout') == 'chart')
            st.metric("Charts", charts)
        with col3:
            tables = sum(1 for s in content.get('slides', []) if s.get('layout') == 'table')
            st.metric("Tables", tables)
        with col4:
            st.metric("Template", "Custom" if st.session_state.template_data and st.session_state.template_data.get('use_template_file') else "Default")
    
    else:
        st.info("Generate content first to export")
        
        st.markdown("""
        ### How to Export:
        1. Go to the **Generate** tab
        2. Enter your presentation topic
        3. Click **Generate**
        4. Return here to download as **PPTX** or **PDF**
        """)


if __name__ == "__main__":
    main()
