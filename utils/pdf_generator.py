"""
PDF Generator - Uses Template Colors Exactly
"""

import io
from typing import Dict, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak


class PDFGenerator:
    """Generates PDF matching template exactly"""
    
    def __init__(self, template_data: Optional[Dict] = None):
        self.template_data = template_data or self._get_defaults()
        self._setup_colors()
    
    def _get_defaults(self) -> Dict:
        return {
            'colors': {
                'background': '#FFFFFF',
                'text_primary': '#000000',
                'text_secondary': '#666666',
                'primary': '#0066CC'
            },
            'fonts': {
                'title': {'size': 32, 'name': 'Helvetica-Bold'},
                'body': {'size': 14, 'name': 'Helvetica'}
            }
        }
    
    def _setup_colors(self):
        """Setup colors from template"""
        self.bg_color = self._hex_to_color(
            self.template_data['colors'].get('background', '#FFFFFF')
        )
        self.text_color = self._hex_to_color(
            self.template_data['colors'].get('text_primary', '#000000')
        )
        self.accent_color = self._hex_to_color(
            self.template_data['colors'].get('primary', '#0066CC')
        )
    
    def _hex_to_color(self, hex_str: str):
        """Convert hex to reportlab color"""
        hex_str = hex_str.lstrip('#')
        r = int(hex_str[0:2], 16) / 255.0
        g = int(hex_str[2:4], 16) / 255.0
        b = int(hex_str[4:6], 16) / 255.0
        return colors.Color(r, g, b)
    
    def generate_pdf(self, content: Dict) -> io.BytesIO:
        """Generate PDF"""
        output = io.BytesIO()
        
        doc = SimpleDocTemplate(
            output,
            pagesize=landscape(LETTER),
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        story = []
        
        # Create styles
        title_style = ParagraphStyle(
            name='Title',
            fontName=self.template_data['fonts']['title']['name'],
            fontSize=self.template_data['fonts']['title']['size'],
            textColor=self.text_color,
            alignment=1,  # Center
            spaceAfter=20
        )
        
        body_style = ParagraphStyle(
            name='Body',
            fontName=self.template_data['fonts']['body']['name'],
            fontSize=self.template_data['fonts']['body']['size'],
            textColor=self.text_color,
            spaceAfter=10,
            leftIndent=20
        )
        
        # Generate slides
        slides = content.get('slides', [])
        
        for i, slide in enumerate(slides):
            # Title
            title = slide.get('title', '')
            if title:
                story.append(Spacer(1, 0.5*inch))
                story.append(Paragraph(title, title_style))
                story.append(Spacer(1, 0.3*inch))
            
            # Content
            slide_content = slide.get('content', {})
            bullets = slide_content.get('bullet_points', [])
            
            for bullet in bullets:
                story.append(Paragraph(f"• {bullet}", body_style))
            
            # Page break
            if i < len(slides) - 1:
                story.append(PageBreak())
        
        # Build with background
        doc.build(
            story,
            onFirstPage=self._add_background,
            onLaterPages=self._add_background
        )
        
        output.seek(0)
        return output
    
    def _add_background(self, canvas, doc):
        """Add background"""
        canvas.saveState()
        canvas.setFillColor(self.bg_color)
        canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=True, stroke=False)
        canvas.restoreState()
