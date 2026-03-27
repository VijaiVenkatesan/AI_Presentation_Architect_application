"""
PDF Generator Module (Cairo-Free)
Converts presentation content to PDF format using ReportLab only
"""

import io
from typing import Dict, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas


class PDFGenerator:
    """Generates PDF from presentation content"""
    
    def __init__(self, template_data: Optional[Dict] = None):
        self.template_data = template_data or self._get_default_template()
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.page_width = landscape(LETTER)[0]
        self.page_height = landscape(LETTER)[1]
    
    def _get_default_template(self) -> Dict:
        return {
            'colors': {
                'primary': '#6366F1',
                'secondary': '#8B5CF6',
                'accent': '#EC4899',
                'background': '#FFFFFF',
                'text_primary': '#1F2937',
                'text_secondary': '#6B7280'
            },
            'fonts': {
                'title': {'name': 'Helvetica-Bold', 'size': 32, 'color': '#1F2937'},
                'subtitle': {'name': 'Helvetica', 'size': 20, 'color': '#6B7280'},
                'body': {'name': 'Helvetica', 'size': 14, 'color': '#1F2937'}
            }
        }
    
    def _hex_to_rgb_tuple(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple (0-1 range)"""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
            return (r, g, b)
        except:
            return (0, 0, 0)
    
    def _hex_to_reportlab_color(self, hex_color: str):
        """Convert hex to reportlab color"""
        r, g, b = self._hex_to_rgb_tuple(hex_color)
        return colors.Color(r, g, b)
    
    def _is_dark_background(self) -> bool:
        """Check if background is dark"""
        bg_hex = self.template_data['colors'].get('background', '#FFFFFF')
        r, g, b = self._hex_to_rgb_tuple(bg_hex)
        # Calculate perceived brightness
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        return brightness < 0.5
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles based on template"""
        
        # Determine if we need light or dark text based on background
        is_dark_bg = self._is_dark_background()
        
        # Title style
        title_color = self._hex_to_reportlab_color(
            self.template_data['fonts']['title'].get('color', 
                '#FFFFFF' if is_dark_bg else '#1F2937')
        )
        
        self.styles.add(ParagraphStyle(
            name='SlideTitle',
            fontName='Helvetica-Bold',
            fontSize=self.template_data['fonts']['title'].get('size', 32),
            textColor=title_color,
            alignment=TA_CENTER,
            spaceAfter=20,
            spaceBefore=10
        ))
        
        # Subtitle style
        subtitle_color = self._hex_to_reportlab_color(
            self.template_data['fonts']['subtitle'].get('color',
                '#CCCCCC' if is_dark_bg else '#6B7280')
        )
        
        self.styles.add(ParagraphStyle(
            name='SlideSubtitle',
            fontName='Helvetica',
            fontSize=self.template_data['fonts']['subtitle'].get('size', 20),
            textColor=subtitle_color,
            alignment=TA_CENTER,
            spaceAfter=15
        ))
        
        # Body style
        body_color = self._hex_to_reportlab_color(
            self.template_data['fonts']['body'].get('color',
                '#F3F4F6' if is_dark_bg else '#1F2937')
        )
        
        self.styles.add(ParagraphStyle(
            name='SlideBody',
            fontName='Helvetica',
            fontSize=self.template_data['fonts']['body'].get('size', 14),
            textColor=body_color,
            alignment=TA_LEFT,
            spaceAfter=10,
            leftIndent=20,
            leading=18
        ))
        
        # Bullet style
        self.styles.add(ParagraphStyle(
            name='SlideBullet',
            fontName='Helvetica',
            fontSize=self.template_data['fonts']['body'].get('size', 14),
            textColor=body_color,
            alignment=TA_LEFT,
            spaceAfter=8,
            leftIndent=40,
            bulletIndent=20,
            leading=18
        ))
    
    def generate_pdf(self, content: Dict) -> io.BytesIO:
        """Generate PDF from presentation content"""
        output = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            output,
            pagesize=landscape(LETTER),
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )
        
        # Build content
        story = []
        slides = content.get('slides', [])
        
        for i, slide in enumerate(slides):
            slide_elements = self._create_slide_elements(slide)
            story.extend(slide_elements)
            
            # Page break between slides (except last)
            if i < len(slides) - 1:
                story.append(PageBreak())
        
        # Build PDF with background
        try:
            doc.build(
                story,
                onFirstPage=self._add_page_background,
                onLaterPages=self._add_page_background
            )
        except Exception as e:
            print(f"Error building PDF: {e}")
            # Fallback without custom background
            doc.build(story)
        
        output.seek(0)
        return output
    
    def _add_page_background(self, canvas_obj, doc):
        """Add background color to each page"""
        try:
            bg_color = self._hex_to_reportlab_color(
                self.template_data['colors'].get('background', '#FFFFFF')
            )
            canvas_obj.saveState()
            canvas_obj.setFillColor(bg_color)
            canvas_obj.rect(
                0, 0,
                self.page_width,
                self.page_height,
                fill=True,
                stroke=False
            )
            canvas_obj.restoreState()
        except Exception as e:
            print(f"Error adding background: {e}")
    
    def _create_slide_elements(self, slide: Dict) -> List:
        """Create PDF elements for a slide"""
        elements = []
        layout = slide.get('layout', 'content')
        
        # Add top spacer
        elements.append(Spacer(1, 0.3*inch))
        
        # Route to appropriate layout creator
        if layout == 'title':
            elements.extend(self._create_title_slide(slide))
        elif layout == 'quote':
            elements.extend(self._create_quote_slide(slide))
        elif layout == 'conclusion':
            elements.extend(self._create_conclusion_slide(slide))
        elif layout == 'metrics':
            elements.extend(self._create_metrics_slide(slide))
        elif layout == 'table':
            elements.extend(self._create_table_slide(slide))
        else:
            elements.extend(self._create_content_slide(slide))
        
        return elements
    
    def _create_title_slide(self, slide: Dict) -> List:
        """Create title slide"""
        elements = []
        
        # Center vertically
        elements.append(Spacer(1, 1.5*inch))
        
        # Title
        title = slide.get('title', 'Presentation Title')
        elements.append(Paragraph(title, self.styles['SlideTitle']))
        
        # Subtitle
        subtitle = slide.get('subtitle', '')
        if subtitle:
            elements.append(Spacer(1, 0.3*inch))
            elements.append(Paragraph(subtitle, self.styles['SlideSubtitle']))
        
        # Decorative line
        elements.append(Spacer(1, 0.2*inch))
        primary_color = self._hex_to_reportlab_color(
            self.template_data['colors'].get('primary', '#6366F1')
        )
        
        line_data = [[''], ['']]
        line_table = Table(line_data, colWidths=[3*inch])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 3, primary_color),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        elements.append(line_table)
        
        return elements
    
    def _create_content_slide(self, slide: Dict) -> List:
        """Create standard content slide"""
        elements = []
        
        # Title
        title = slide.get('title', '')
        if title:
            elements.append(Paragraph(title, self.styles['SlideTitle']))
            elements.append(Spacer(1, 0.2*inch))
        
        # Content
        content_data = slide.get('content', {})
        
        # Bullet points
        bullet_points = content_data.get('bullet_points', [])
        if bullet_points:
            for point in bullet_points:
                bullet_html = f"<bullet>&bull;</bullet> {point}"
                elements.append(Paragraph(bullet_html, self.styles['SlideBullet']))
        
        # Main text
        main_text = content_data.get('main_text', '')
        if main_text:
            elements.append(Paragraph(main_text, self.styles['SlideBody']))
        
        # Two column content
        left_col = content_data.get('left_column', '')
        right_col = content_data.get('right_column', '')
        
        if left_col or right_col:
            elements.extend(self._create_two_column(left_col, right_col))
        
        return elements
    
    def _create_two_column(self, left_content, right_content) -> List:
        """Create two-column layout"""
        elements = []
        
        # Process left content
        left_items = []
        if isinstance(left_content, list):
            for item in left_content:
                left_items.append(Paragraph(f"• {item}", self.styles['SlideBullet']))
        elif left_content:
            left_items.append(Paragraph(str(left_content), self.styles['SlideBody']))
        
        # Process right content
        right_items = []
        if isinstance(right_content, list):
            for item in right_content:
                right_items.append(Paragraph(f"• {item}", self.styles['SlideBullet']))
        elif right_content:
            right_items.append(Paragraph(str(right_content), self.styles['SlideBody']))
        
        # Create table for columns
        if left_items or right_items:
            # Pad to same length
            max_len = max(len(left_items), len(right_items))
            while len(left_items) < max_len:
                left_items.append('')
            while len(right_items) < max_len:
                right_items.append('')
            
            col_data = [[left_items[i], right_items[i]] for i in range(max_len)]
            
            col_table = Table(col_data, colWidths=[3.5*inch, 3.5*inch])
            col_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            
            elements.append(col_table)
        
        return elements
    
    def _create_quote_slide(self, slide: Dict) -> List:
        """Create quote slide"""
        elements = []
        
        content_data = slide.get('content', {})
        quote = content_data.get('quote', '')
        author = content_data.get('quote_author', '')
        
        # Vertical spacing
        elements.append(Spacer(1, 1.5*inch))
        
        # Quote style
        quote_color = self._hex_to_reportlab_color(
            self.template_data['colors'].get('text_primary', '#1F2937')
        )
        
        quote_style = ParagraphStyle(
            name='QuoteText',
            fontName='Helvetica-Oblique',
            fontSize=24,
            textColor=quote_color,
            alignment=TA_CENTER,
            spaceAfter=20,
            leading=32
        )
        
        # Quote with marks
        quote_text = f'"{quote}"'
        elements.append(Paragraph(quote_text, quote_style))
        
        # Author
        if author:
            author_color = self._hex_to_reportlab_color(
                self.template_data['colors'].get('text_secondary', '#6B7280')
            )
            
            author_style = ParagraphStyle(
                name='QuoteAuthor',
                fontName='Helvetica',
                fontSize=16,
                textColor=author_color,
                alignment=TA_RIGHT,
                leftIndent=2*inch
            )
            elements.append(Paragraph(f"— {author}", author_style))
        
        return elements
    
    def _create_conclusion_slide(self, slide: Dict) -> List:
        """Create conclusion slide"""
        elements = []
        
        # Vertical spacing
        elements.append(Spacer(1, 1*inch))
        
        # Title
        title = slide.get('title', 'Thank You')
        elements.append(Paragraph(title, self.styles['SlideTitle']))
        elements.append(Spacer(1, 0.5*inch))
        
        # Bullet points
        content_data = slide.get('content', {})
        bullet_points = content_data.get('bullet_points', [])
        
        if bullet_points:
            # Center bullets for conclusion
            centered_style = ParagraphStyle(
                name='CenteredBullet',
                parent=self.styles['SlideBullet'],
                alignment=TA_CENTER,
                leftIndent=0,
                bulletIndent=0
            )
            
            for point in bullet_points:
                elements.append(Paragraph(f"• {point}", centered_style))
        
        # Call to action
        cta = content_data.get('call_to_action', '')
        if cta:
            elements.append(Spacer(1, 0.3*inch))
            accent_color = self._hex_to_reportlab_color(
                self.template_data['colors'].get('accent', '#EC4899')
            )
            cta_style = ParagraphStyle(
                name='CTA',
                fontName='Helvetica-Bold',
                fontSize=16,
                textColor=accent_color,
                alignment=TA_CENTER
            )
            elements.append(Paragraph(cta, cta_style))
        
        return elements
    
    def _create_metrics_slide(self, slide: Dict) -> List:
        """Create metrics slide"""
        elements = []
        
        # Title
        title = slide.get('title', 'Key Metrics')
        elements.append(Paragraph(title, self.styles['SlideTitle']))
        elements.append(Spacer(1, 0.5*inch))
        
        # Metrics
        content_data = slide.get('content', {})
        metrics = content_data.get('key_metrics', [])
        
        if metrics:
            # Create metrics table
            metric_rows = []
            values_row = []
            labels_row = []
            
            for metric in metrics[:4]:
                values_row.append(Paragraph(
                    f"<b>{metric.get('value', '')}</b>",
                    ParagraphStyle(
                        name='MetricValue',
                        fontName='Helvetica-Bold',
                        fontSize=28,
                        textColor=self._hex_to_reportlab_color(
                            self.template_data['colors'].get('accent', '#EC4899')
                        ),
                        alignment=TA_CENTER
                    )
                ))
                labels_row.append(Paragraph(
                    metric.get('label', ''),
                    ParagraphStyle(
                        name='MetricLabel',
                        fontName='Helvetica',
                        fontSize=12,
                        textColor=self._hex_to_reportlab_color(
                            self.template_data['colors'].get('text_secondary', '#6B7280')
                        ),
                        alignment=TA_CENTER
                    )
                ))
            
            metric_rows = [values_row, labels_row]
            
            col_width = 7*inch / len(metrics[:4])
            metric_table = Table(metric_rows, colWidths=[col_width] * len(metrics[:4]))
            
            metric_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 15),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ]))
            
            elements.append(metric_table)
        
        return elements
    
    def _create_table_slide(self, slide: Dict) -> List:
        """Create table slide"""
        elements = []
        
        # Title
        title = slide.get('title', '')
        if title:
            elements.append(Paragraph(title, self.styles['SlideTitle']))
            elements.append(Spacer(1, 0.2*inch))
        
        # Table
        content_data = slide.get('content', {})
        table_info = content_data.get('table', {})
        
        headers = table_info.get('headers', [])
        rows = table_info.get('rows', [])
        
        if headers:
            # Build table data
            table_data = [headers] + rows
            
            # Calculate column widths
            num_cols = len(headers)
            col_width = 7*inch / num_cols
            
            # Create table
            pdf_table = Table(table_data, colWidths=[col_width] * num_cols)
            
            # Style table
            primary_color = self._hex_to_reportlab_color(
                self.template_data['colors'].get('primary', '#6366F1')
            )
            text_color = self._hex_to_reportlab_color(
                self.template_data['colors'].get('text_primary', '#1F2937')
            )
            
            style = TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), primary_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                
                # Data rows
                ('BACKGROUND', (0, 1), (-1, -1), colors.Color(0.95, 0.95, 0.95)),
                ('TEXTCOLOR', (0, 1), (-1, -1), text_color),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.7, 0.7, 0.7)),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                
                # Alternate row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [
                    colors.Color(0.95, 0.95, 0.95),
                    colors.Color(0.9, 0.9, 0.9)
                ]),
            ])
            
            pdf_table.setStyle(style)
            elements.append(pdf_table)
        
        return elements
