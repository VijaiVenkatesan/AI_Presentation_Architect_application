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
from utils.pdf_generator import PDFGenerator

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
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #F8FAFC !important;
    }
    
    /* Cards */
    .info-card {
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #475569;
        margin: 0.5rem 0;
    }
    
    /* Template Info Card */
    .template-card {
        background: linear-gradient(135deg, #065F46 0%, #047857 100%);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        border: 1px solid #10B981;
        margin: 1rem 0;
    }
    
    /* Color swatch */
    .color-swatch {
        display: inline-block;
        width: 24px;
        height: 24px;
        border-radius: 4px;
        border: 2px solid #fff;
        margin-right: 8px;
        vertical-align: middle;
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
    
    /* Danger button */
    .danger-btn button {
        background: linear-gradient(135deg, #DC2626 0%, #EF4444 100%) !important;
    }
    
    /* Success button */
    .success-btn button {
        background: linear-gradient(135deg, #059669 0%, #10B981 100%) !important;
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
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: #1E293B;
        border-radius: 8px;
    }
    
    /* Layout row */
    .layout-row {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin: 0.5rem 0;
    }
    
    .layout-badge {
        background: #334155;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        color: #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    defaults = {
        'content': None,
        'template_data': None,
        'template_file_name': None,
        'generated': False,
        'chat_history': [],
        'current_slide': 0
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_all_data():
    """Clear all session data"""
    st.session_state.content = None
    st.session_state.template_data = None
    st.session_state.template_file_name = None
    st.session_state.generated = False
    st.session_state.chat_history = []
    st.session_state.current_slide = 0


def clear_generated_content():
    """Clear only generated content, keep template"""
    st.session_state.content = None
    st.session_state.generated = False
    st.session_state.current_slide = 0


def main():
    """Main application"""
    
    initialize_session_state()
    
    # Initialize handlers
    llm_handler = LLMHandler()
    template_analyzer = TemplateAnalyzer()
    search_handler = SearchHandler()
    
    # Render sidebar and get configuration
    config = render_sidebar(llm_handler)
    
    # Main content area - Header
    col1, col2, col3 = st.columns([6, 2, 2])
    
    with col1:
        st.markdown("""
        <h1 style="
            background: linear-gradient(135deg, #6366F1 0%, #EC4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2rem;
            font-weight: 800;
            margin: 0;
        ">🎯 AI Presentation Architect</h1>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("🔄 Clear Content", use_container_width=True):
            clear_generated_content()
            st.rerun()
    
    with col3:
        if st.button("🗑️ Reset All", use_container_width=True, type="secondary"):
            clear_all_data()
            st.rerun()
    
    st.markdown("<p style='color: #94A3B8; margin-top: -10px;'>Create stunning enterprise presentations with AI</p>", unsafe_allow_html=True)
    
    # Status indicators row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if llm_handler.is_configured():
            st.success("✓ AI Connected")
        else:
            st.warning("⚠ Add API Key")
    
    with col2:
        if st.session_state.template_data and st.session_state.template_data.get('use_template_file'):
            st.success(f"✓ Template: {st.session_state.template_file_name or 'Loaded'}")
        else:
            st.info("○ No Template")
    
    with col3:
        if st.session_state.content:
            slide_count = len(st.session_state.content.get('slides', []))
            st.success(f"✓ {slide_count} Slides Ready")
        else:
            st.info(f"○ {config.get('num_slides', 10)} Slides (Target)")
    
    with col4:
        if config.get('selected_model'):
            model_name = config['selected_model'].split('-')[0].title()
            st.info(f"🤖 {model_name}")
    
    st.divider()
    
    # ============================================
    # TEMPLATE UPLOAD AND ANALYSIS
    # ============================================
    
    if config.get('template_file'):
        file_name = config['template_file'].name
        
        # Check if this is a new template
        if st.session_state.template_file_name != file_name:
            with st.spinner("📊 Analyzing template..."):
                config['template_file'].seek(0)
                file_bytes = io.BytesIO(config['template_file'].read())
                config['template_file'].seek(0)
                
                if file_name.endswith('.pptx'):
                    st.session_state.template_data = template_analyzer.analyze_pptx(file_bytes)
                else:
                    st.session_state.template_data = template_analyzer.analyze_image(file_bytes)
                
                st.session_state.template_file_name = file_name
    
    # Show Template Information Card
    if st.session_state.template_data and st.session_state.template_data.get('use_template_file'):
        td = st.session_state.template_data
        
        st.markdown("""
        <div class="template-card">
            <h4 style="margin:0; color: white;">✓ Template Loaded Successfully</h4>
            <p style="margin:5px 0 0 0; color: #A7F3D0; font-size: 0.9rem;">
                Your generated presentation will use this template's exact styling
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("📋 Template Details", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**📐 Dimensions**")
                st.markdown(f"Width: `{td['slide_size']['width']:.2f}\"`")
                st.markdown(f"Height: `{td['slide_size']['height']:.2f}\"`")
                
                st.markdown("**🖼️ Logo**")
                if td.get('has_logo'):
                    st.markdown("✓ Logo detected")
                    pos = td.get('logo_position', {})
                    st.markdown(f"Position: ({pos.get('left', 0):.1f}\", {pos.get('top', 0):.1f}\")")
                else:
                    st.markdown("No logo detected")
            
            with col2:
                st.markdown("**🎨 Detected Colors**")
                colors_data = td.get('colors', {})
                
                for color_name, color_value in colors_data.items():
                    st.markdown(
                        f'<div style="display:flex; align-items:center; margin:4px 0;">'
                        f'<span class="color-swatch" style="background:{color_value};"></span>'
                        f'<span>{color_name}: {color_value}</span></div>',
                        unsafe_allow_html=True
                    )
            
            with col3:
                st.markdown("**📝 Detected Fonts**")
                fonts_data = td.get('fonts', {})
                
                for font_type, font_info in fonts_data.items():
                    font_name = font_info.get('name', 'Arial')
                    font_size = font_info.get('size', 18)
                    st.markdown(f"**{font_type.title()}**: {font_name} ({font_size}pt)")
                
                st.markdown("**📑 Available Layouts**")
                layouts = td.get('slide_layouts_info', [])
                if layouts:
                    layout_names = [l.get('name', 'Unknown') for l in layouts[:5]]
                    for name in layout_names:
                        st.markdown(f"• {name}")
                    if len(layouts) > 5:
                        st.markdown(f"*+ {len(layouts) - 5} more...*")
    
    # ============================================
    # MAIN TABS
    # ============================================
    
    tab1, tab2, tab3, tab4 = st.tabs(["💬 Generate", "✏️ Edit", "👁️ Preview", "💾 Export"])
    
    # ============================================
    # TAB 1: GENERATE
    # ============================================
    with tab1:
        st.markdown("### Create Your Presentation")
        
        # Chat interface
        user_prompt = render_chat_interface(
            llm_handler,
            config.get('selected_model', 'llama-3.3-70b-versatile')
        )
        
        if user_prompt:
            with st.spinner("🚀 Generating presentation content..."):
                # Fetch real-time data if enabled
                real_time_data = None
                if config.get('include_real_time_data'):
                    with st.status("Searching for real-time data...") as status:
                        real_time_data = search_handler.compile_research_data(user_prompt)
                        status.update(label="✓ Data compiled", state="complete")
                
                # Get template context
                template_context = st.session_state.template_data or template_analyzer._get_default_template()
                
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
                slide_count = len(content.get('slides', []))
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': f"✓ Created presentation '{content.get('title', 'Untitled')}' with {slide_count} slides."
                })
            
            st.success(f"✓ Generated {len(content.get('slides', []))} slides!")
            st.rerun()
        
        # Show current content summary
        if st.session_state.content:
            content = st.session_state.content
            
            st.divider()
            st.markdown("### 📋 Generated Presentation")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Title", content.get('title', 'Untitled')[:25] + "...")
            with col2:
                st.metric("Slides", len(content.get('slides', [])))
            with col3:
                st.metric("Template", "Custom" if st.session_state.template_data and st.session_state.template_data.get('use_template_file') else "Default")
            with col4:
                st.metric("Status", "✓ Ready")
            
            # Slide overview
            with st.expander("📊 Slide Overview", expanded=False):
                layout_emojis = {
                    'title': '🎯', 'content': '📝', 'two_column': '📊',
                    'chart': '📈', 'table': '📋', 'quote': '💬',
                    'timeline': '⏰', 'comparison': '⚖️', 'conclusion': '🎬',
                    'metrics': '📊', 'image': '🖼️'
                }
                
                for slide in content.get('slides', []):
                    layout = slide.get('layout', 'content')
                    emoji = layout_emojis.get(layout, '📄')
                    title = slide.get('title', 'Untitled')
                    st.markdown(f"{emoji} **Slide {slide.get('slide_number', '?')}** ({layout}): {title}")
    
    # ============================================
    # TAB 2: EDIT
    # ============================================
    with tab2:
        if st.session_state.content:
            st.session_state.content = render_editor(st.session_state.content)
        else:
            st.info("💡 Generate content first to edit slides")
            st.markdown("""
            **How to get started:**
            1. Upload a template (optional but recommended)
            2. Go to the **Generate** tab
            3. Describe your presentation topic
            4. Click **Generate**
            5. Come back here to edit
            """)
    
    # ============================================
    # TAB 3: PREVIEW
    # ============================================
    with tab3:
        if st.session_state.content:
            # Get template data for preview colors
            template_data = st.session_state.template_data or None
            render_preview(st.session_state.content, template_data)
        else:
            st.info("💡 Generate content first to see preview")
    
    # ============================================
    # TAB 4: EXPORT
    # ============================================
    with tab4:
        st.markdown("### 💾 Export Your Presentation")
        
        if st.session_state.content:
            content = st.session_state.content
            
            col1, col2 = st.columns(2)
            
            # PPTX Export
            with col1:
                st.markdown("""
                <div class="info-card">
                    <h4 style="margin:0; color: #F8FAFC;">📊 PowerPoint Export</h4>
                    <p style="color: #94A3B8; margin: 8px 0;">Download as .pptx file with template styling</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("📥 Generate PowerPoint", use_container_width=True, type="primary"):
                    with st.spinner("Creating PowerPoint..."):
                        try:
                            template_data = st.session_state.template_data or {}
                            
                            generator = PresentationGenerator(template_data)
                            pptx_file = generator.generate_presentation(content)
                            
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"presentation_{timestamp}.pptx"
                            
                            st.download_button(
                                label="⬇️ Download PPTX",
                                data=pptx_file,
                                file_name=filename,
                                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                use_container_width=True
                            )
                            
                            st.success("✓ PowerPoint generated!")
                        except Exception as e:
                            st.error(f"Error generating PPTX: {e}")
            
            # PDF Export
            with col2:
                st.markdown("""
                <div class="info-card">
                    <h4 style="margin:0; color: #F8FAFC;">📄 PDF Export</h4>
                    <p style="color: #94A3B8; margin: 8px 0;">Download as PDF document</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("📥 Generate PDF", use_container_width=True):
                    with st.spinner("Creating PDF..."):
                        try:
                            template_data = st.session_state.template_data or {}
                            
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
                            
                            st.success("✓ PDF generated!")
                        except Exception as e:
                            st.error(f"Error generating PDF: {e}")
            
            st.divider()
            
            # Export Summary
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
                has_template = st.session_state.template_data and st.session_state.template_data.get('use_template_file')
                st.metric("Template", "Custom ✓" if has_template else "Default")
            
            # Template Info in Export
            if st.session_state.template_data and st.session_state.template_data.get('use_template_file'):
                st.info("✓ Your exported presentation will use the uploaded template's styling, layouts, colors, and fonts.")
        
        else:
            st.info("💡 Generate content first to export")
            
            st.markdown("""
            ### How to Export:
            1. **Upload a template** (optional) in the sidebar
            2. Go to the **Generate** tab
            3. Enter your presentation topic
            4. Click **Generate**
            5. Return here to download as **PPTX** or **PDF**
            """)


if __name__ == "__main__":
    main()
