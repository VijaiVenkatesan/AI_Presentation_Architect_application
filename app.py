"""AI Presentation Architect - Main Application"""
import streamlit as st
import os
import sys
import logging
import json
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from components.sidebar import render_sidebar
from components.editor import render_slide_editor
from components.preview import display_all_slides_preview, render_slide_preview
from components.chat_interface import render_chat_interface
from utils.llm_handler import LLMHandler
from utils.ppt_generator import EnhancedPPTGenerator
from utils.pdf_generator import EnhancedPDFGenerator
from utils.validation import SlideValidator
from utils.config import AppConfig
from utils.file_handler import save_template_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler('app.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

st.set_page_config(page_title="AI Presentation Architect", page_icon="", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.main-header { font-size: 2.5rem; color: #4F81BD; font-weight: bold; margin-bottom: 1rem; }
.status-badge { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.875rem; font-weight: 500; }
.status-ready { background: #d4edda; color: #155724; }
.status-processing { background: #fff3cd; color: #856404; }
.export-section { background: #f8f9fa; border-radius: 8px; padding: 1rem; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    defaults = {
        'slides': [], 'presentation_title': '', 'presentation_topic': '',
        'template_file': None, 'template_path': None, 'current_slide_index': 0,
        'generation_in_progress': False, 'api_configured': False, 'llm_handler': None,
        'config': None, 'validation_result': None, 'last_saved': None,
        'groq_api_key': '', 'num_slides': 10, 'chat_history': [],
        'pending_message': None, 'use_template': False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def load_configuration():
    try:
        config = AppConfig.from_file()
        st.session_state.config = config
        if config.groq_api_key:
            st.session_state.llm_handler = LLMHandler(api_key=config.groq_api_key)
            st.session_state.api_configured = True
            logger.info("LLM handler initialized")
        else:
            st.session_state.llm_handler = LLMHandler()
            st.session_state.api_configured = False
            logger.warning("GROQ_API_KEY not configured")
        return True
    except Exception as e:
        logger.error(f"Config error: {e}")
        st.session_state.config = AppConfig()
        st.session_state.llm_handler = LLMHandler()
        st.session_state.api_configured = False
        return True


def auto_save_presentation():
    try:
        save_data = {
            'title': st.session_state.presentation_title,
            'topic': st.session_state.presentation_topic,
            'slides': st.session_state.slides,
            'timestamp': datetime.now().isoformat(),
        }
        st.session_state.last_saved = datetime.now()
        Path('.cache').mkdir(exist_ok=True)
        with open('.cache/autosave.json', 'w') as f:
            json.dump(save_data, f, indent=2)
    except Exception as e:
        logger.warning(f"Auto-save failed: {e}")


def load_autosave():
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
                return True
        except Exception as e:
            logger.warning(f"Failed to load autosave: {e}")
    return False


def generate_presentation_content(prompt, num_slides):
    if not st.session_state.api_configured:
        st.error("API not configured. Set GROQ_API_KEY in secrets.")
        return False
    try:
        llm = st.session_state.llm_handler
        progress_bar = st.progress(0)
        status_text = st.empty()

        status_text.info("Planning presentation...")
        progress_bar.progress(20)

        outline_prompt = f"""Create a presentation outline for: {prompt}
Requirements:
- Exactly {num_slides} slides
- Use layouts: title, content, two_column, chart, table, quote, metrics, image, timeline, conclusion
- Return valid JSON array with: slide_number, layout, title, content
Return ONLY the JSON array, no markdown."""

        outline_response = llm.generate_structured_response(prompt=outline_prompt)
        if not outline_response:
            raise ValueError("Failed to generate outline")

        if isinstance(outline_response, list):
            slides_list = outline_response
        elif isinstance(outline_response, dict):
            slides_list = outline_response.get('slides', outline_response.get('data', outline_response.get('presentation', [])))
            if not isinstance(slides_list, list):
                slides_list = [outline_response]
        else:
            raise ValueError(f"Unexpected response type: {type(outline_response)}")

        if not slides_list:
            raise ValueError("Empty slides list")

        progress_bar.progress(40)
        status_text.info("Generating slide content...")

        generated_slides = []
        for i, slide_outline in enumerate(slides_list[:num_slides]):
            if not isinstance(slide_outline, dict):
                continue
            if 'content' not in slide_outline or not isinstance(slide_outline.get('content'), dict):
                slide_outline['content'] = {}
            slide_outline['slide_number'] = i + 1
            if 'title' not in slide_outline:
                slide_outline['title'] = f"Slide {i+1}"
            if 'layout' not in slide_outline:
                slide_outline['layout'] = 'content'
            generated_slides.append(slide_outline)
            progress_bar.progress(40 + (i + 1) * 60 // min(len(slides_list), num_slides))
            time.sleep(0.2)

        if not generated_slides:
            raise ValueError("No valid slides generated")

        progress_bar.progress(90)
        status_text.info("Validating...")

        validation = SlideValidator.validate_slides(generated_slides)
        st.session_state.validation_result = validation

        st.session_state.slides = generated_slides
        st.session_state.presentation_title = st.session_state.presentation_title or prompt[:50]

        progress_bar.progress(100)
        status_text.success(f"Generated {len(generated_slides)} slides!")

        auto_save_presentation()
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()
        return True

    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        st.error(f"Error: {str(e)}")
        return False


def export_presentation(format_type, use_template=True):
    if not st.session_state.slides:
        st.error("No slides to export")
        return None
    try:
        validation = SlideValidator.validate_slides(st.session_state.slides)
        if validation['errors']:
            st.error("Fix validation errors first")
            return None
        if validation['warnings']:
            st.info(f"{len(validation['warnings'])} minor issues - export will use fallback layouts")

        status_text = st.empty()
        progress_bar = st.progress(0)

        template_path = None
        if use_template and st.session_state.get('template_path'):
            template_path = st.session_state.template_path

        if format_type == 'pptx':
            status_text.info("Creating PowerPoint..." + (" (with template)" if template_path else ""))
            generator = EnhancedPPTGenerator(template_path=template_path)
            progress_bar.progress(50)
            output = generator.generate(st.session_state.slides)
            progress_bar.progress(100)
            status_text.success("PPTX ready!" + (" Template applied!" if template_path else ""))
            return output
        elif format_type == 'pdf':
            status_text.info("Creating PDF...")
            generator = EnhancedPDFGenerator()
            progress_bar.progress(50)
            output = generator.generate(st.session_state.slides)
            progress_bar.progress(100)
            status_text.success("PDF ready!")
            return output
    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        st.error(f"Export error: {str(e)}")
        return None
    finally:
        time.sleep(0.3)
        if 'progress_bar' in locals():
            progress_bar.empty()
        if 'status_text' in locals():
            status_text.empty()


def display_generation_stats():
    slides = st.session_state.slides
    if not slides:
        return
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Slides", len(slides))
    with col2:
        st.metric("Layouts", len({s.get('layout') for s in slides}))
    with col3:
        st.metric("Charts", sum(1 for s in slides if s.get('layout') == 'chart'))
    with col4:
        st.metric("Tables", sum(1 for s in slides if s.get('layout') == 'table'))


def main():
    initialize_session_state()
    load_configuration()
    if not st.session_state.slides:
        load_autosave()

    sidebar_result = render_sidebar()

    if sidebar_result.get('generate', False):
        topic = sidebar_result.get('topic', '')
        num_slides = sidebar_result.get('num_slides', 10)
        if topic:
            with st.spinner("Generating presentation..."):
                if generate_presentation_content(topic, num_slides):
                    st.rerun()

    st.markdown('<h1 class="main-header">AI Presentation Architect</h1>', unsafe_allow_html=True)

    status = "Ready" if st.session_state.slides else "Start"
    badge_class = "status-ready" if st.session_state.slides else "status-processing"
    st.markdown(f'<span class="status-badge {badge_class}">{status}</span>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["Editor", "Preview", "AI Chat", "Export"])

    with tab1:
        st.subheader("Slide Editor")
        if not st.session_state.slides:
            st.info("Configure in sidebar and click Generate")
        else:
            display_generation_stats()
            st.divider()
            render_slide_editor()
            if st.session_state.last_saved:
                st.caption(f"Auto-saved at {st.session_state.last_saved.strftime('%H:%M:%S')}")

    with tab2:
        st.subheader("Live Preview")
        if not st.session_state.slides:
            st.info("Generate slides first")
        else:
            if st.button("Refresh Preview"):
                st.rerun()
            st.divider()
            display_all_slides_preview(st.session_state.slides)

    with tab3:
        st.subheader("AI Chat Assistant")
        if not st.session_state.api_configured:
            st.warning("Set GROQ_API_KEY to enable chat")
        else:
            render_chat_interface()

    with tab4:
        st.subheader("Export Presentation")
        if not st.session_state.slides:
            st.info("Generate slides first")
        else:
            st.markdown('<div class="export-section">', unsafe_allow_html=True)

            if st.session_state.get('template_path') and st.session_state.get('use_template'):
                st.success(f"Using template: {Path(st.session_state.template_path).name}")
            elif st.session_state.get('template_path'):
                st.info("Template uploaded but not enabled - check sidebar")
            else:
                st.info("Using default PowerPoint template")

            if st.session_state.validation_result:
                val = st.session_state.validation_result
                if val['valid']:
                    st.success("All slides passed validation")
                else:
                    st.error(f"{len(val['errors'])} error(s) found")
                if val['warnings']:
                    with st.expander(f"{len(val['warnings'])} warnings"):
                        for warn in val['warnings']:
                            st.caption(f"• {warn}")

            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### PowerPoint (.pptx)")
                st.caption("Editable format with full layout support")
                if st.button("Export as PPTX", type="primary", use_container_width=True):
                    data = export_presentation('pptx', use_template=st.session_state.get('use_template', False))
                    if data:
                        st.download_button(
                            label="Download PPTX", data=data,
                            file_name=f"{st.session_state.presentation_title or 'presentation'}.pptx",
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            use_container_width=True)
            with col2:
                st.markdown("### PDF Document (.pdf)")
                st.caption("Print-ready format")
                if st.button("Export as PDF", type="primary", use_container_width=True):
                    data = export_presentation('pdf', use_template=False)
                    if 
                        st.download_button(
                            label="Download PDF", data=data,
                            file_name=f"{st.session_state.presentation_title or 'presentation'}.pdf",
                            mime="application/pdf", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    st.caption(
        f"AI Presentation Architect • "
        f"{len(st.session_state.slides)} slides • "
        f"API: {'Connected' if st.session_state.api_configured else 'Not configured'} • "
        f"Template: {'Active' if st.session_state.get('template_path') and st.session_state.get('use_template') else 'Not used'}"
    )

    if st.session_state.slides and st.session_state.last_saved:
        if (datetime.now() - st.session_state.last_saved).total_seconds() > 120:
            auto_save_presentation()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Application crashed: {e}", exc_info=True)
        st.error("Application error occurred. Please refresh the page.")
        st.exception(e)
