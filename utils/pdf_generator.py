"""
Enhanced PDF Generator - Generates from slide data, not screenshots
"""
from typing import Dict, List, Any, Optional
from pathlib import Path
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.colors import HexColor, black, grey, blue
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
import logging

logger = logging.getLogger(__name__)

class EnhancedPDFGenerator:
    """Professional PDF generator from slide data"""
    
    def __init__(self, page_size=A4):
        self.page_size = page_size
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Create custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='SlideTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#4F81BD'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SlideContent',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=black,
            spaceAfter=10,
            alignment=TA_LEFT,
            fontName='Helvetica'
        ))
        
        self.styles.add(ParagraphStyle(
            name='BulletPoint',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=black,
            leftIndent=20,
            spaceAfter=5,
            fontName='Helvetica'
        ))
        
        self.styles.add(ParagraphStyle(
            name='Quote',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=grey,
            leftIndent=40,
            rightIndent=40,
            spaceAfter=15,
            alignment=TA_JUSTIFY,
            fontName='Helvetica-Oblique'
        ))
        
        self.styles.add(ParagraphStyle(
            name='Metric',
            parent=self.styles['Normal'],
            fontSize=28,
            textColor=HexColor('#4F81BD'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
    
    def generate(self, slides_data: List[Dict[str, Any]], output_path: Optional[str] = None) -> io.BytesIO:
        """
        Generate PDF from slide data
        
        Args:
            slides_data: List of slide dictionaries
            output_path: Optional file path to save PDF
        
        Returns:
            BytesIO object with PDF
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        for slide_data in slides_data:
            try:
                slide_elements = self._create_slide_elements(slide_data)
                story.extend(slide_elements)
                story.append(Spacer(1, 0.5*inch))  # Space between slides
                story.append(self._add_page_break())
            except Exception as e:
                logger.error(f"Failed to create slide {slide_data.get('slide_number')}: {e}", exc_info=True)
                # Add error placeholder
                story.append(Paragraph(f"⚠️ Slide {slide_data.get('slide_number')} - Generation Error", self.styles['SlideTitle']))
                story.append(Spacer(1, 0.2*inch))
        
        doc.build(story)
        buffer.seek(0)
        
        return buffer
    
    def _create_slide_elements(self, slide_data: Dict[str, Any]) -> List:
        """Create PDF elements for a single slide"""
        elements = []
        layout = slide_data.get('layout', 'content')
        
        # Add slide title
        if slide_data.get('title'):
            elements.append(Paragraph(slide_data['title'], self.styles['SlideTitle']))
            elements.append(Spacer(1, 0.2*inch))
        
        # Route to specific layout handler
        handler = getattr(self, f'_handle_{layout}_pdf', self._handle_content_pdf)
        elements.extend(handler(slide_data))
        
        return elements
    
    def _handle_content_pdf(self, slide_data: Dict[str, Any]) -> List:
        """Handle content layout"""
        elements = []
        content = slide_data.get('content', {})
        
        if content.get('main_text'):
            elements.append(Paragraph(content['main_text'], self.styles['SlideContent']))
            elements.append(Spacer(1, 0.1*inch))
        
        for bullet in content.get('bullet_points', []):
            elements.append(Paragraph(f"• {bullet}", self.styles['BulletPoint']))
        
        return elements
    
    def _handle_two_column_pdf(self, slide_data: Dict[str, Any]) -> List:
        """Handle two-column layout"""
        elements = []
        content = slide_data.get('content', {})
        
        # Create two-column table
        left_content = content.get('left_column', '')
        right_content = content.get('right_column', '')
        
        # Format as lists if strings
        if isinstance(left_content, str):
            left_items = [left_content]
        else:
            left_items = left_content
        
        if isinstance(right_content, str):
            right_items = [right_content]
        else:
            right_items = right_content
        
        # Create table data
        table_data = [
            [
                '\n'.join([f"• {item}" for item in left_items]),
                '\n'.join([f"• {item}" for item in right_items])
            ]
        ]
        
        table = Table(table_data, colWidths=[3.5*inch, 3.5*inch])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(table)
        return elements
    
    def _handle_chart_pdf(self, slide_data: Dict[str, Any]) -> List:
        """Handle chart layout"""
        elements = []
        content = slide_data.get('content', {})
        chart_data = content.get('chart', {})
        
        if chart_data.get('title'):
            elements.append(Paragraph(f"📊 {chart_data['title']}", self.styles['SlideContent']))
            elements.append(Spacer(1, 0.1*inch))
        
        if chart_data.get('description'):
            elements.append(Paragraph(chart_data['description'], self.styles['SlideContent']))
            elements.append(Spacer(1, 0.1*inch))
        
        # Add chart data as table
        if chart_data.get('data'):
            table_data = [['Metric', 'Value']]
            for key, value in chart_data['data'].items():
                table_data.append([key, str(value)])
            
            table = Table(table_data, colWidths=[3*inch, 3*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#4F81BD')),
                ('TEXTCOLOR', (0, 0), (-1, 0), black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, black)
            ]))
            elements.append(table)
        
        return elements
    
    def _handle_table_pdf(self, slide_data: Dict[str, Any]) -> List:
        """Handle table layout"""
        elements = []
        content = slide_data.get('content', {})
        table_data = content.get('table', {})
        
        if table_data.get('headers'):
            data = [table_data['headers']]
            data.extend(table_data.get('data', []))
            
            table = Table(data, colWidths=[2*inch] * len(table_data['headers']))
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#4F81BD')),
                ('TEXTCOLOR', (0, 0), (-1, 0), black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, black)
            ]))
            elements.append(table)
        
        return elements
    
    def _handle_quote_pdf(self, slide_data: Dict[str, Any]) -> List:
        """Handle quote layout"""
        elements = []
        content = slide_data.get('content', {})
        
        quote_text = content.get('quote', '')
        quote_author = content.get('quote_author', '')
        
        elements.append(Paragraph(f""{quote_text}"", self.styles['Quote']))
        
        if quote_author:
            elements.append(Paragraph(f"— {quote_author}", self.styles['BulletPoint']))
        
        return elements
    
    def _handle_metrics_pdf(self, slide_data: Dict[str, Any]) -> List:
        """Handle metrics/KPI layout"""
        elements = []
        content = slide_data.get('content', {})
        metrics = content.get('key_metrics', [])
        
        # Create metrics table
        table_data = []
        for metric in metrics:
            table_data.append([
                Paragraph(metric.get('value', 'N/A'), self.styles['Metric']),
                Paragraph(metric.get('label', ''), self.styles['SlideContent'])
            ])
        
        table = Table(table_data, colWidths=[2.5*inch, 3.5*inch])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        elements.append(table)
        
        return elements
    
    def _handle_image_pdf(self, slide_data: Dict[str, Any]) -> List:
        """Handle image layout"""
        elements = []
        content = slide_data.get('content', {})
        image_data = content.get('image', '')
        
        if image_data:
            try:
                # Handle base64 image
                if isinstance(image_data, str) and image_data.startswith('data:image'):
                    import base64
                    import re
                    match = re.search(r'data:image/\w+;base64,(.+)', image_data)
                    if match:
                        img_bytes = base64.b64decode(match.group(1))
                        img_buffer = io.BytesIO(img_bytes)
                        img = Image(img_buffer, width=5*inch, height=3.5*inch)
                        elements.append(img)
                elif Path(image_data).exists():
                    img = Image(image_data, width=5*inch, height=3.5*inch)
                    elements.append(img)
            except Exception as e:
                logger.error(f"Failed to add image to PDF: {e}")
                elements.append(Paragraph("🖼️ Image placeholder (failed to load)", self.styles['SlideContent']))
        
        return elements
    
    def _handle_timeline_pdf(self, slide_data: Dict[str, Any]) -> List:
        """Handle timeline layout"""
        elements = []
        content = slide_data.get('content', {})
        timeline_items = content.get('timeline_items', [])
        
        for item in timeline_items:
            date = item.get('date', '')
            desc = item.get('description', '')
            
            elements.append(Paragraph(f"📅 {date}", self.styles['SlideContent']))
            elements.append(Paragraph(desc, self.styles['BulletPoint']))
            elements.append(Spacer(1, 0.1*inch))
        
        return elements
    
    def _handle_conclusion_pdf(self, slide_data: Dict[str, Any]) -> List:
        """Handle conclusion layout"""
        elements = []
        content = slide_data.get('content', {})
        
        if content.get('main_text'):
            elements.append(Paragraph(content['main_text'], self.styles['SlideTitle']))
            elements.append(Spacer(1, 0.1*inch))
        
        for bullet in content.get('bullet_points', []):
            elements.append(Paragraph(f"✓ {bullet}", self.styles['BulletPoint']))
        
        return elements
    
    def _add_page_break(self):
        """Add page break"""
        from reportlab.platypus import PageBreak
        return PageBreak()
