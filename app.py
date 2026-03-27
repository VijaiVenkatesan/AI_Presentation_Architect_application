"""
AI Presentation Architect - Main Application Entry Point
Version 2.0 - Fixed all import and configuration issues
"""
import streamlit as st
import os
import sys
import logging
import json
import time
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import custom modules
from components.sidebar import render_sidebar
from components.editor import render_slide_editor
from components.preview import display_all_slides_preview, render_slide_preview
from components.chat_interface import render_chat_interface
from utils.llm_handler import LLMHandler
from utils.template_analyzer import TemplateAnalyzer
from utils.ppt_generator import EnhancedPPTGenerator
from utils.pdf_generator import EnhancedPDFGenerator
from utils.validation import SlideValidator
from utils.config import AppConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="🎨 AI Presentation Architect",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4F81BD;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.875rem;
        font-weight: 500;
    }
    .status-ready { background: #d4edda; color: #155724; }
    .status-processing { background: #fff3cd; color: #856404; }
    .status-error { background: #f8d7da; color: #721c24; }
    .slide-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .export-section {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'slides': [],
        'presentation_title': '',
        'presentation_topic': '',
        'template_file': None,
        'template_analyzed': False,
        'current_slide_index': 0,
        'generation_in_progress': False,
        'export_format': None,
        'api_configured': False,
        'llm_handler': None,
        'config': None,
        'validation_result': None,
        'error_messages': [],
        'success_messages': [],
        'last_saved': None,
        'groq_api_key': '',
        'num_slides': 10,
        'chat_history': [],
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def load_configuration():
    """Load application configuration"""
    try:
        config = AppConfig.from_file()
        st.session_state.config = config
        
        # Initialize LLM handler
        if config.groq_api_key:
            st.session_state.llm_handler = LLMHandler(api_key=config.groq_api_key)
            st.session_state.api_configured = True
            logger.info("LLM handler initialized successfully")
        else:
            st.session_state.llm_handler = LLMHandler()
            st.session_state.api_configured = False
            logger.warning("GROQ_API_KEY not configured - AI features disabled")
        
        return True
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}", exc_info=True)
        st.warning(f"⚠️ Configuration warning: {str(e)}")
        st.session_state.config = AppConfig()
        st.session_state.llm_handler = LLMHandler()
        st.session_state.api_configured = False
        return True


def auto_save_presentation():
    """Auto-save presentation state to prevent data loss"""
    try:
        save_data = {
            'title': st.session_state.presentation_title,
            'topic': st.session_state.presentation_topic,
            'slides': st.session_state.slides,
            'timestamp': datetime.now().isoformat(),
            'version': '2.0'
        }
        
        st.session_state.last_saved = datetime.now()
        
        cache_dir = Path('.cache')
        cache_dir.mkdir(exist_ok=True)
        save_path = cache_dir / 'autosave.json'
        
        with open(save_path, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        logger.debug(f"Auto-saved presentation to {save_path}")
        
    except Exception as e:
        logger.warning(f"Auto-save failed: {e}")


def load_autosave():
    """Load auto-saved presentation if available"""
    cache_path = Path('.cache/autosave.json')
    
    if cache_path.exists():
        try:
            with open(cache_path) as f:
                data = json.load(f)
            
            saved_time = datetime.fromisoformat(data.get('timestamp', ''))
            if (datetime.now() - saved_time).total_seconds() < 86400:
                st.session_state.presentation_title = data.get('title', '')
                st.session_state.presentation_topic = data.get('topic', '')
                st.session_state.slides = data.get('slides', [])
                st.session_state.last_saved = saved_time
                
                logger.info(f"Loaded auto-saved presentation from {saved_time}")
                return True
        except Exception as e:
            logger.warning(f"Failed to load autosave: {e}")
    
    return False


def generate_presentation_content(prompt: str, num_slides: int, template_data: Optional[Dict] = None) -> bool:
    """
    Generate presentation content using LLM
    
    Args:
        prompt: User's presentation topic/prompt
        num_slides: Number of slides to generate
        template_data: Optional template analysis data
    
    Returns:
        bool: Success status
    """
    if not st.session_state.api_configured:
        st.error("❌ API not configured. Please set GROQ_API_KEY in sidebar or environment.")
        return False
    
    try:
        llm = st.session_state.llm_handler
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.info("🔄 Analyzing prompt and planning structure...")
        progress_bar.progress(20)
        
        outline_prompt = f"""
        Create a presentation outline for: {prompt}
        
        Requirements:
        - Exactly {num_slides} slides
        - Include diverse layouts: title, content, two_column, chart, table, quote, metrics, image, timeline, conclusion
        - Each slide should have: title, layout type, content structure
        - Return valid JSON array only
        
        Example format:
        [
            {{"slide_number": 1, "layout": "title", "title": "Main Title", "content": {{"subtitle": "..."}}}},
            {{"slide_number": 2, "layout": "content", "title": "Intro", "content": {{"main_text": "...", "bullet_points": ["..."]}}}}
        ]
        """
        
        outline_response = llm.generate_structured_response(
            prompt=outline_prompt,
            response_format={"type": "json_object"}
        )
        
        if not outline_response:
            raise ValueError("Failed to generate slide outline")
        
        progress_bar.progress(40)
        status_text.info("🔄 Generating detailed slide content...")
        
        generated_slides = []
        slides_list = outline_response.get('slides', outline_response) if isinstance(outline_response, dict) else outline_response
        
        if not isinstance(slides_list, list):
            slides_list = [outline_response]
        
        for i, slide_outline in enumerate(slides_list[:num_slides]):
            status_text.info(f"🔄 Generating slide {i+1}/{min(len(slides_list), num_slides)}: {slide_outline.get('title', 'Untitled')}")
            
            detail_prompt = f"""
            Expand this slide with rich, professional content:
            
            Slide {slide_outline.get('slide_number', i+1)}: {slide_outline.get('title')}
            Layout: {slide_outline.get('layout')}
            Topic: {prompt}
            
            Generate appropriate content based on layout type.
            Return valid JSON with: title, layout, content, speaker_notes
            """
            
            slide_content = llm.generate_structured_response(
                prompt=detail_prompt,
                response_format={"type": "json_object"}
            )
            
            if slide_content:
                slide_content['slide_number'] = i + 1
                generated_slides.append(slide_content)
            
            progress_bar.progress(40 + (i + 1) * 60 // min(len(slides_list), num_slides))
            time.sleep(0.3)
        
        progress_bar.progress(90)
        status_text.info("🔄 Validating and formatting slides...")
        
        validation = SlideValidator.validate_slides(generated_slides)
        st.session_state.validation_result = validation
        
        if validation['errors']:
            logger.warning(f"Validation errors: {validation['errors']}")
            for error in validation['errors']:
                st.warning(f"⚠️ {error}")
        
        st.session_state.slides = generated_slides
        st.session_state.presentation_title = st.session_state.presentation_title or prompt[:50]
        
        progress_bar.progress(100)
        status_text.success("✅ Presentation generated successfully!")
        
        auto_save_presentation()
        
        time.sleep(1)
        progress_bar.empty()
        status_text.empty()
        
        return True
        
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        st.error(f"❌ Generation error: {str(e)}")
        return False


def export_presentation(format_type: str) -> Optional[bytes]:
    """
    Export presentation to PPTX or PDF
    
    Args:
        format_type: 'pptx' or 'pdf'
    
    Returns:
        Bytes object with file content or None
    """
    if not st.session_state.slides:
        st.error("❌ No slides to export. Generate content first.")
        return None
    
    try:
        validation = SlideValidator.validate_slides(st.session_state.slides)
        
        if validation['errors']:
            st.error("❌ Cannot export - validation errors found:")
            for error in validation['errors']:
                st.error(f"  • {error}")
            return None
        
        if validation['warnings']:
            st.warning(f"⚠️ {len(validation['warnings'])} warnings - export may have issues:")
            for warning in validation['warnings'][:3]:
                st.warning(f"  • {warning}")
        
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        if format_type == 'pptx':
            status_text.info("📊 Generating PowerPoint presentation...")
            generator = EnhancedPPTGenerator()
            progress_bar.progress(50)
            
            output = generator.generate(st.session_state.slides)
            
            progress_bar.progress(100)
            status_text.success("✅ PowerPoint file ready!")
            
            return output
            
        elif format_type == 'pdf':
            status_text.info("📄 Generating PDF document...")
            generator = EnhancedPDFGenerator()
            progress_bar.progress(50)
            
            output = generator.generate(st.session_state.slides)
            
            progress_bar.progress(100)
            status_text.success("✅ PDF file ready!")
            
            return output
        
    except Exception as e:
        logger.error(f"Export failed ({format_type}): {e}", exc_info=True)
        st.error(f"❌ Export error: {str(e)}")
        return None
    finally:
        time.sleep(0.5)
        if 'progress_bar' in locals():
            progress_bar.empty()
        if 'status_text' in locals():
            status_text.empty()


def display_generation_stats():
    """Display presentation statistics"""
    slides = st.session_state.slides
    
    if not slides:
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Slides", len(slides))
    
    with col2:
        layouts = {s.get('layout', 'content') for s in slides}
        st.metric("🎨 Layout Types", len(layouts))
    
    with col3:
        has_charts = sum(1 for s in slides if s.get('layout') == 'chart')
        st.metric("📈 Charts", has_charts)
    
    with col4:
        has_tables = sum(1 for s in slides if s.get('layout') == 'table')
        st.metric("📋 Tables", has_tables)
    
    with st.expander("📐 Layout Distribution", expanded=False):
        layout_counts = {}
        for slide in slides:
            layout = slide.get('layout', 'content')
            layout_counts[layout] = layout_counts.get(layout, 0) + 1
        
        col_a, col_b = st.columns([2, 1])
        with col_a:
            for layout, count in sorted(layout_counts.items()):
                st.write(f"• **{layout}**: {count} slide{'s' if count > 1 else ''}")
        with col_b:
            if layout_counts:
                st.bar_chart(layout_counts)


def main():
    """Main application entry point"""
    
    initialize_session_state()
    
    if not load_configuration():
        st.stop()
    
    if not st.session_state.slides:
        load_autosave()
    
    render_sidebar()
    
    st.markdown('<h1 class="main-header">🎨 AI Presentation Architect</h1>', unsafe_allow_html=True)
    
    status_class = "status-ready" if st.session_state.slides else "status-processing"
    status_text = "✓ Ready" if st.session_state.slides else "⏳ Start creating"
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem;">
        <span class="status-badge {status_class}">{status_text}</span>
        {f'<span style="color: #666; font-size: 0.9rem;">Last saved: {st.session_state.last_saved.strftime("%H:%M") if st.session_state.last_saved else "Never"}</span>' if st.session_state.last_saved else ''}
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["✏️ Editor", "👁️ Preview", "💬 AI Assistant", "📥 Export"])
    
    with tab1:
        st.subheader("📝 Slide Editor")
        
        if not st.session_state.slides:
            st.info("👈 Use the sidebar to configure your presentation and click 'Generate' to create slides")
        else:
            display_generation_stats()
            st.divider()
            render_slide_editor()
            
            if st.session_state.last_saved:
                st.caption(f"💾 Auto-saved at {st.session_state.last_saved.strftime('%H:%M:%S')}")
    
    with tab2:
        st.subheader("👁️ Live Preview")
        
        if not st.session_state.slides:
            st.info("Generate slides first to see preview")
        else:
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🔄 Refresh Preview", use_container_width=True):
                    st.rerun()
            
            with col1:
                st.caption(f"Previewing {len(st.session_state.slides)} slide{'s' if len(st.session_state.slides) > 1 else ''}")
            
            st.divider()
            display_all_slides_preview(st.session_state.slides)
    
    with tab3:
        st.subheader("💬 AI Chat Assistant")
        
        if not st.session_state.api_configured:
            st.warning("⚠️ Configure GROQ_API_KEY to enable AI chat features")
        else:
            render_chat_interface()
    
    with tab4:
        st.subheader("📥 Export Presentation")
        
        if not st.session_state.slides:
            st.info("Generate slides first to enable export")
        else:
            st.markdown('<div class="export-section">', unsafe_allow_html=True)
            
            if st.session_state.validation_result:
                val = st.session_state.validation_result
                if val['valid']:
                    st.success("✅ All slides passed validation")
                else:
                    st.error(f"❌ {len(val['errors'])} error(s) found - fix before exporting")
                if val['warnings']:
                    st.warning(f"⚠️ {len(val['warnings'])} warning(s) - review recommended")
            
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📊 PowerPoint (.pptx)")
                st.caption("Editable format with full layout support")
                
                if st.button("📥 Export as PPTX", use_container_width=True, type="primary"):
                    pptx_data = export_presentation('pptx')
                    if pptx_data:
                        st.download_button(
                            label="⬇️ Download PowerPoint File",
                            data=pptx_data,
                            file_name=f"{st.session_state.presentation_title or 'presentation'}.pptx",
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            use_container_width=True
                        )
            
            with col2:
                st.markdown("### 📄 PDF Document (.pdf)")
                st.caption("Print-ready format with consistent formatting")
                
                if st.button("📥 Export as PDF", use_container_width=True, type="primary"):
                    pdf_data = export_presentation('pdf')
                    if pdf_data:
                        st.download_button(
                            label="⬇️ Download PDF File",
                            data=pdf_data,
                            file_name=f"{st.session_state.presentation_title or 'presentation'}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            with st.expander("💡 Export Tips"):
                st.markdown("""
                - **PPTX**: Best for further editing in PowerPoint or Google Slides
                - **PDF**: Best for sharing, printing, or presentations where editing isn't needed
                - Charts and tables are rendered as native PowerPoint/PDF elements
                - Images are embedded at high resolution
                - Speaker notes are included in PPTX (view in Notes pane)
                """)
    
    st.divider()
    st.caption(
        "🎨 AI Presentation Architect v2.0 • "
        f"Slides: {len(st.session_state.slides)} • "
        f"API: {'✅ Connected' if st.session_state.api_configured else '❌ Not configured'}"
    )
    
    if st.session_state.slides and st.session_state.last_saved:
        elapsed = (datetime.now() - st.session_state.last_saved).total_seconds()
        if elapsed > 120:
            auto_save_presentation()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Application crashed: {e}", exc_info=True)
        st.error("💥 Application error occurred. Please check logs or refresh the page.")
        st.exception(e)
