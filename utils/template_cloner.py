"""
Template Cloner - Preserves Template Exactly
Uses the uploaded template as-is and only modifies content
"""

import io
import copy
from typing import Dict, List, Optional, Any
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN


class TemplateCloner:
    """Clones template and fills with new content while preserving all styling"""
    
    def __init__(self, template_bytes: Optional[bytes] = None):
        self.template_bytes = template_bytes
        self.prs = None
        self.available_layouts = []
        
        if template_bytes:
            self._load_template()
    
    def _load_template(self):
        """Load the template presentation"""
        try:
            template_stream = io.BytesIO(self.template_bytes)
            self.prs = Presentation(template_stream)
            
            # Get available layouts
            self.available_layouts = []
            for idx, layout in enumerate(self.prs.slide_layouts):
                self.available_layouts.append({
                    'index': idx,
                    'name': layout.name,
                    'layout': layout
                })
        except Exception as e:
            print(f"Error loading template: {e}")
            self.prs = Presentation()
    
    def generate_presentation(self, content: Dict) -> io.BytesIO:
        """Generate presentation using template"""
        
        if not self.prs:
            self._load_template()
        
        if not self.prs:
            # Fallback to blank presentation
            self.prs = Presentation()
        
        # Clear existing slides while keeping masters
        self._clear_content_slides()
        
        # Generate new slides from content
        slides_data = content.get('slides', [])
        
        for slide_data in slides_data:
            self._add_slide_from_content(slide_data)
        
        # Save to BytesIO
        output = io.BytesIO()
        self.prs.save(output)
        output.seek(0)
        
        return output
    
    def _clear_content_slides(self):
        """Remove all content slides but keep masters"""
        try:
            # Remove slides from end to beginning
            slide_count = len(self.prs.slides)
            
            for _ in range(slide_count):
                if len(self.prs.slides) > 0:
                    # Get first slide's ID
                    xml_slides = self.prs.slides._sldIdLst
                    if len(xml_slides) > 0:
                        slide_id = xml_slides[0]
                        # Remove relationship
                        try:
                            self.prs.part.drop_rel(slide_id.rId)
                        except:
                            pass
                        # Remove from list
                        xml_slides.remove(slide_id)
        except Exception as e:
            print(f"Warning: Could not clear slides: {e}")
    
    def _add_slide_from_content(self, slide_data: Dict):
        """Add a slide using template layout and fill with content"""
        
        layout_type = slide_data.get('layout', 'content')
        
        # Get appropriate layout
        layout = self._get_layout_for_type(layout_type)
        
        # Add slide
        slide = self.prs.slides.add_slide(layout)
        
        # Fill placeholders with content
        self._fill_slide_content(slide, slide_data)
    
    def _get_layout_for_type(self, layout_type: str):
        """Get the best matching layout from template"""
        
        # Layout name patterns
        layout_patterns = {
            'title': ['title slide', 'title', 'cover'],
            'content': ['title and content', 'content', 'bullet', 'text'],
            'two_column': ['two content', 'comparison', 'two column', 'side by side'],
            'chart': ['title and content', 'content', 'chart'],
            'table': ['title and content', 'content', 'table'],
            'quote': ['blank', 'quote', 'title only'],
            'conclusion': ['title slide', 'section header', 'conclusion'],
            'metrics': ['title and content', 'content'],
            'timeline': ['title and content', 'content'],
            'comparison': ['comparison', 'two content'],
            'image': ['picture with caption', 'content', 'picture']
        }
        
        preferred = layout_patterns.get(layout_type, ['title and content'])
        
        # Try to find matching layout
        for pattern in preferred:
            for layout_info in self.available_layouts:
                if pattern.lower() in layout_info['name'].lower():
                    return layout_info['layout']
        
        # Fallback: use first available layout
        if self.available_layouts:
            # For title slides, use first layout
            if layout_type == 'title':
                return self.available_layouts[0]['layout']
            # For others, try to use second layout (usually content)
            elif len(self.available_layouts) > 1:
                return self.available_layouts[1]['layout']
            else:
                return self.available_layouts[0]['layout']
        
        # Last resort: use any layout
        return self.prs.slide_layouts[0]
    
    def _fill_slide_content(self, slide, slide_data: Dict):
        """Fill slide placeholders with actual content"""
        
        title_text = slide_data.get('title', '')
        subtitle_text = slide_data.get('subtitle', '')
        content_data = slide_data.get('content', {})
        
        # Track which placeholders we've filled
        filled_placeholders = set()
        
        # Fill placeholders
        for shape in slide.shapes:
            try:
                if not hasattr(shape, 'is_placeholder'):
                    continue
                
                if not shape.is_placeholder:
                    continue
                
                placeholder_type = str(shape.placeholder_format.type)
                
                # Title placeholder
                if 'TITLE' in placeholder_type or 'CENTER_TITLE' in placeholder_type:
                    if shape.has_text_frame and title_text:
                        self._set_text_preserve_format(shape.text_frame, title_text)
                        filled_placeholders.add('title')
                
                # Subtitle placeholder
                elif 'SUBTITLE' in placeholder_type:
                    if shape.has_text_frame and subtitle_text:
                        self._set_text_preserve_format(shape.text_frame, subtitle_text)
                        filled_placeholders.add('subtitle')
                
                # Body/Content placeholder
                elif 'BODY' in placeholder_type or 'OBJECT' in placeholder_type:
                    if shape.has_text_frame:
                        # Get bullet points or main text
                        bullet_points = content_data.get('bullet_points', [])
                        main_text = content_data.get('main_text', '')
                        
                        if bullet_points:
                            self._set_bullets_preserve_format(shape.text_frame, bullet_points)
                            filled_placeholders.add('content')
                        elif main_text:
                            self._set_text_preserve_format(shape.text_frame, main_text)
                            filled_placeholders.add('content')
                
            except Exception as e:
                # Continue with other shapes even if one fails
                continue
        
        # If no placeholders were filled, add text boxes manually
        if 'title' not in filled_placeholders and title_text:
            self._add_fallback_title(slide, title_text)
        
        if 'content' not in filled_placeholders:
            bullet_points = content_data.get('bullet_points', [])
            if bullet_points:
                self._add_fallback_content(slide, bullet_points)
    
    def _set_text_preserve_format(self, text_frame, text: str):
        """Set text while preserving formatting"""
        try:
            # Clear existing paragraphs
            text_frame.clear()
            
            # Add new text
            p = text_frame.paragraphs[0]
            p.text = text
            
            # Preserve alignment if it exists
            # Font formatting is inherited from the placeholder
            
        except Exception as e:
            print(f"Error setting text: {e}")
    
    def _set_bullets_preserve_format(self, text_frame, bullet_points: List[str]):
        """Set bullet points while preserving formatting"""
        try:
            # Clear existing
            text_frame.clear()
            
            # Add bullet points
            for i, point in enumerate(bullet_points):
                if i == 0:
                    p = text_frame.paragraphs[0]
                else:
                    p = text_frame.add_paragraph()
                
                p.text = point
                p.level = 0
                
                # The bullet style is inherited from the placeholder
                
        except Exception as e:
            print(f"Error setting bullets: {e}")
    
    def _add_fallback_title(self, slide, title: str):
        """Add title as text box if no placeholder found"""
        try:
            # Get slide dimensions
            slide_width = self.prs.slide_width
            slide_height = self.prs.slide_height
            
            # Add title text box at top
            left = Inches(0.5)
            top = Inches(0.5)
            width = slide_width - Inches(1)
            height = Inches(1)
            
            txBox = slide.shapes.add_textbox(left, top, width, height)
            tf = txBox.text_frame
            p = tf.paragraphs[0]
            p.text = title
            p.font.size = Pt(32)
            p.font.bold = True
            
        except Exception as e:
            print(f"Error adding fallback title: {e}")
    
    def _add_fallback_content(self, slide, bullet_points: List[str]):
        """Add content as text box if no placeholder found"""
        try:
            # Get slide dimensions
            slide_width = self.prs.slide_width
            
            # Add content below title
            left = Inches(0.75)
            top = Inches(2)
            width = slide_width - Inches(1.5)
            height = Inches(4)
            
            txBox = slide.shapes.add_textbox(left, top, width, height)
            tf = txBox.text_frame
            
            for i, point in enumerate(bullet_points):
                if i == 0:
                    p = tf.paragraphs[0]
                else:
                    p = tf.add_paragraph()
                
                p.text = f"• {point}"
                p.font.size = Pt(18)
                
        except Exception as e:
            print(f"Error adding fallback content: {e}")
    
    def get_template_info(self) -> Dict:
        """Get information about the loaded template"""
        if not self.prs:
            return {}
        
        return {
            'slide_width': self.prs.slide_width.inches,
            'slide_height': self.prs.slide_height.inches,
            'num_layouts': len(self.available_layouts),
            'layouts': [{'name': l['name'], 'index': l['index']} for l in self.available_layouts],
            'num_masters': len(self.prs.slide_masters)
        }
