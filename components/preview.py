"""
Preview Component - Fixed Deprecation Warnings
"""

import streamlit as st
from typing import Dict, List
from PIL import Image

from utils.preview_handler import PreviewHandler


def render_preview(content: Dict, template_data: Dict) -> None:
    """Render the presentation preview with template colors"""
    
    if not content or 'slides' not in content:
        st.info("Generate content to see preview")
        return
    
    # Info about preview
    if template_data and template_data.get('use_template_file'):
        st.info("🎨 Preview uses colors from your uploaded template. The actual exported file will match your template exactly.")
    else:
        st.info("🎨 Preview shows default styling. Upload a template for custom styling.")
    
    # Create preview handler with template data
    preview_handler = PreviewHandler(template_data)
    
    # Generate previews
    with st.spinner("Generating preview..."):
        previews = preview_handler.generate_previews(content)
    
    if not previews:
        st.warning("Could not generate previews")
        return
    
    # View mode selection
    col1, col2 = st.columns([3, 1])
    
    with col1:
        view_mode = st.radio(
            "View Mode",
            ["Single Slide", "Grid View"],
            horizontal=True,
            label_visibility="collapsed"
        )
    
    with col2:
        if st.button("🔄 Refresh Preview"):
            st.rerun()
    
    st.divider()
    
    if view_mode == "Single Slide":
        render_single_view(content, previews)
    else:
        render_grid_view(content, previews)


def render_single_view(content: Dict, previews: List[Image.Image]) -> None:
    """Render single slide view"""
    
    if 'current_slide' not in st.session_state:
        st.session_state.current_slide = 0
    
    idx = st.session_state.current_slide
    
    # Ensure index is valid
    if idx >= len(previews):
        idx = 0
        st.session_state.current_slide = 0
    
    # Navigation
    col1, col2, col3, col4, col5 = st.columns([1, 1, 4, 1, 1])
    
    with col1:
        if st.button("⏮️ First", disabled=idx == 0):
            st.session_state.current_slide = 0
            st.rerun()
    
    with col2:
        if st.button("◀️ Prev", disabled=idx == 0):
            st.session_state.current_slide -= 1
            st.rerun()
    
    with col3:
        st.markdown(
            f"<p style='text-align:center; color:#94A3B8; font-size:1.1rem; margin:0;'>"
            f"<strong>Slide {idx + 1}</strong> of {len(previews)}</p>",
            unsafe_allow_html=True
        )
    
    with col4:
        if st.button("Next ▶️", disabled=idx >= len(previews) - 1):
            st.session_state.current_slide += 1
            st.rerun()
    
    with col5:
        if st.button("Last ⏭️", disabled=idx >= len(previews) - 1):
            st.session_state.current_slide = len(previews) - 1
            st.rerun()
    
    # Display slide - FIXED: use width instead of use_container_width
    if 0 <= idx < len(previews):
        st.image(previews[idx], width="stretch")
        
        # Slide info
        slide = content['slides'][idx]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Title:** {slide.get('title', 'Untitled')}")
        
        with col2:
            st.markdown(f"**Layout:** {slide.get('layout', 'content').title()}")
    
    # Thumbnail strip
    st.divider()
    st.markdown("**All Slides:**")
    
    cols = st.columns(min(len(previews), 8))
    
    for i, col in enumerate(cols):
        if i < len(previews):
            with col:
                thumb = previews[i].resize((160, 90))
                
                if st.button(f"{i+1}", key=f"thumb_{i}", use_container_width=True):
                    st.session_state.current_slide = i
                    st.rerun()
                
                # FIXED: use width instead of use_container_width
                st.image(thumb, width="stretch")


def render_grid_view(content: Dict, previews: List[Image.Image]) -> None:
    """Render grid view of all slides"""
    
    cols_per_row = 3
    
    for row_start in range(0, len(previews), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for i, col in enumerate(cols):
            slide_idx = row_start + i
            
            if slide_idx < len(previews):
                with col:
                    # Slide preview - FIXED: use width instead of use_container_width
                    thumb = previews[slide_idx].resize((400, 225))
                    st.image(thumb, width="stretch")
                    
                    # Slide info
                    slide = content['slides'][slide_idx]
                    st.caption(
                        f"**{slide_idx + 1}. {slide.get('title', 'Untitled')[:30]}**\n"
                        f"Layout: {slide.get('layout', 'content')}"
                    )
