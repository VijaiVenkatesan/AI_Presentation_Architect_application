"""
PowerPoint Generator - Template Preservation
"""

import io
from typing import Dict, Optional
from .template_cloner import TemplateCloner


class PresentationGenerator:
    """Generates presentations using template cloning for perfect preservation"""
    
    def __init__(self, template_data: Optional[Dict] = None):
        self.template_data = template_data or {}
    
    def generate_presentation(
        self,
        content: Dict,
        custom_settings: Optional[Dict] = None
    ) -> io.BytesIO:
        """Generate presentation using template cloning"""
        
        # Check if we have template bytes
        template_bytes = self.template_data.get('template_bytes')
        
        if template_bytes and self.template_data.get('use_template_file'):
            # Use template cloner for perfect preservation
            cloner = TemplateCloner(template_bytes)
            return cloner.generate_presentation(content)
        else:
            # Fallback to basic presentation
            from pptx import Presentation
            from pptx.util import Inches, Pt
            
            prs = Presentation()
            slides_data = content.get('slides', [])
            
            for slide_data in slides_data:
                slide = prs.slides.add_slide(prs.slide_layouts[1])
                
                # Add title
                if slide.shapes.title:
                    slide.shapes.title.text = slide_data.get('title', '')
                
                # Add content
                for shape in slide.placeholders:
                    if shape.placeholder_format.idx == 1:  # Content placeholder
                        tf = shape.text_frame
                        content_data = slide_data.get('content', {})
                        bullets = content_data.get('bullet_points', [])
                        
                        if bullets:
                            tf.clear()
                            for i, bullet in enumerate(bullets):
                                if i == 0:
                                    p = tf.paragraphs[0]
                                else:
                                    p = tf.add_paragraph()
                                p.text = bullet
                                p.level = 0
            
            output = io.BytesIO()
            prs.save(output)
            output.seek(0)
            return output
