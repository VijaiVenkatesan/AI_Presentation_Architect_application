"""
Editor Component
"""

import streamlit as st
from typing import Dict, List


def render_editor(content: Dict) -> Dict:
    """Render the slide editor interface"""
    
    if not content or 'slides' not in content:
        st.info("Generate content first to edit slides")
        return content
    
    st.markdown("### ✏️ Slide Editor")
    
    slide_options = [f"Slide {s['slide_number']}: {s.get('title', 'Untitled')[:30]}" for s in content['slides']]
    
    selected_idx = st.selectbox("Select Slide", range(len(slide_options)), format_func=lambda x: slide_options[x])
    
    if selected_idx is not None:
        slide = content['slides'][selected_idx]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            slide['title'] = st.text_input("Title", value=slide.get('title', ''), key=f"title_{selected_idx}")
            
            layouts = ['title', 'content', 'two_column', 'chart', 'table', 'image', 'quote', 'comparison', 'timeline', 'conclusion', 'metrics']
            current = slide.get('layout', 'content')
            slide['layout'] = st.selectbox("Layout", layouts, index=layouts.index(current) if current in layouts else 1, key=f"layout_{selected_idx}")
        
        with col2:
            st.markdown("#### Actions")
            
            if st.button("📋 Duplicate", key=f"dup_{selected_idx}", use_container_width=True):
                new_slide = slide.copy()
                new_slide['slide_number'] = len(content['slides']) + 1
                content['slides'].append(new_slide)
                st.rerun()
            
            if st.button("🗑️ Delete", key=f"del_{selected_idx}", use_container_width=True):
                if len(content['slides']) > 1:
                    content['slides'].pop(selected_idx)
                    for i, s in enumerate(content['slides']):
                        s['slide_number'] = i + 1
                    st.rerun()
        
        st.divider()
        
        # Content editing
        st.markdown("#### Content")
        
        slide_content = slide.get('content', {})
        
        if slide['layout'] in ['content', 'conclusion']:
            bullet_points = slide_content.get('bullet_points', [])
            edited_points = []
            
            for i, point in enumerate(bullet_points):
                new_point = st.text_input(f"Point {i+1}", value=point, key=f"bullet_{selected_idx}_{i}")
                if new_point:
                    edited_points.append(new_point)
            
            new_point = st.text_input("Add new point", key=f"new_bullet_{selected_idx}")
            if new_point:
                edited_points.append(new_point)
            
            slide_content['bullet_points'] = edited_points
        
        elif slide['layout'] == 'two_column':
            col1, col2 = st.columns(2)
            
            with col1:
                left = slide_content.get('left_column', '')
                if isinstance(left, list):
                    left = '\n'.join(left)
                new_left = st.text_area("Left Column", value=left, height=150, key=f"left_{selected_idx}")
                slide_content['left_column'] = new_left.split('\n') if '\n' in new_left else new_left
            
            with col2:
                right = slide_content.get('right_column', '')
                if isinstance(right, list):
                    right = '\n'.join(right)
                new_right = st.text_area("Right Column", value=right, height=150, key=f"right_{selected_idx}")
                slide_content['right_column'] = new_right.split('\n') if '\n' in new_right else new_right
        
        elif slide['layout'] == 'quote':
            slide_content['quote'] = st.text_area("Quote", value=slide_content.get('quote', ''), key=f"quote_{selected_idx}")
            slide_content['quote_author'] = st.text_input("Author", value=slide_content.get('quote_author', ''), key=f"author_{selected_idx}")
        
        # Speaker notes
        st.markdown("#### 🎤 Speaker Notes")
        slide['speaker_notes'] = st.text_area("Notes", value=slide.get('speaker_notes', ''), height=80, key=f"notes_{selected_idx}")
        
        slide['content'] = slide_content
        content['slides'][selected_idx] = slide
    
    return content
