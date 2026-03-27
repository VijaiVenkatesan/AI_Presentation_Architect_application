"""
PDF Generator Module - Fixed Font Handling
Uses only ReportLab built-in fonts
"""

import io
from typing import Dict, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, 
    Table, TableStyle, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class PDFGenerator:
    """Generates PDF from presentation content using built-in fonts"""
    
    # ReportLab built-in fonts only
    FONTS = {
        'title': 'Helvetica-Bold',
        'subtitle': 'Helvetica',
        'body': 'Helvetica',
        'bold': 'Helvetica-Bold',
        'italic': 'Helvetica-Oblique'
    }
    
    def __init__(self, template_data: Optional[Dict] = None):
        self.template_data = template_data or self._get_defaults()
        self._setup_colors()
    
    def _get_defaults(self) -> Dict:
        return {
            'colors': {
                'background': '#FFFFFF',
                'text_primary': '#1F2937',
                'text_secondary': '#6B7280',
                'primary': '#2563EB',
                'accent': '#EF4444'
            },
            'fonts': {
                'title': {'size': 32},
                'subtitle': {'size': 22},
                'body': {'size': 14}
            }
        }
    
    def _setup_colors(self):
        """Setup colors from template"""
        template_colors = self.template_data.get('colors', {})
        
        self.bg_color = self._hex_to_color(
            template_colors.get('background', '#FFFFFF')
        )
        self.text_color = self._hex_to_color(
            template_colors.get('text_primary', '#1F2937')
        )
        self.secondary_color = self._hex_to_color(
            template_colors.get('text_secondary', '#6B7280')
        )
        self.accent_color = self._hex_to_color(
            template_colors.get('primary', '#2563EB')
        )
        self.highlight_color = self._hex_to_color(
            template_colors.get('accent', '#EF4444')
        )
    
    def _hex_to_color(self, hex_str: str):
        """Convert hex to reportlab color"""
        try:
            hex_str = hex_str.lstrip('#')
            r = int(hex_str[0:2], 16) / 255.0
            g = int(hex_str[2:4], 16) / 255.0
            b = int(hex_str[4:6], 16) / 255.0
            return colors.Color(r, g, b)
        except:
            return colors.black
    
    def _get_font_size(self, font_type: str, default: int) -> int:
        """Get font size from template or use default"""
        fonts = self.template_data.get('fonts', {})
        font_info = fonts.get(font_type, {})
        return font_info.get('size', default)
    
    def generate_pdf(self, content: Dict) -> io.BytesIO:
        """Generate PDF from presentation content"""
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
        slides = content.get('slides', [])
        
        for i, slide in enumerate(slides):
            try:
                slide_elements = self._create_slide_elements(slide)
                story.extend(slide_elements)
                
                # Page break between slides
                if i < len(slides) - 1:
                    story.append(PageBreak())
            except Exception as e:
                print(f"Error creating slide {i}: {e}")
                # Add error placeholder
                story.append(Paragraph(
                    f"[Slide {i+1}: Error rendering]",
                    self._get_body_style()
                ))
                if i < len(slides) - 1:
                    story.append(PageBreak())
        
        # Build PDF
        try:
            doc.build(
                story,
                onFirstPage=self._add_background,
                onLaterPages=self._add_background
            )
        except Exception as e:
            print(f"Error building PDF with background: {e}")
            # Fallback without background
            doc.build(story)
        
        output.seek(0)
        return output
    
    def _add_background(self, canvas, doc):
        """Add background color"""
        try:
            canvas.saveState()
            canvas.setFillColor(self.bg_color)
            canvas.rect(0, 0, doc.pagesize[0], doc.pagesize[1], fill=True, stroke=False)
            canvas.restoreState()
        except:
            pass
    
    def _get_title_style(self) -> ParagraphStyle:
        """Get title paragraph style"""
        return ParagraphStyle(
            name='PDFTitle',
            fontName=self.FONTS['title'],
            fontSize=self._get_font_size('title', 32),
            textColor=self.text_color,
            alignment=TA_CENTER,
            spaceAfter=20,
            spaceBefore=10,
            leading=38
        )
    
    def _get_subtitle_style(self) -> ParagraphStyle:
        """Get subtitle paragraph style"""
        return ParagraphStyle(
            name='PDFSubtitle',
            fontName=self.FONTS['subtitle'],
            fontSize=self._get_font_size('subtitle', 22),
            textColor=self.secondary_color,
            alignment=TA_CENTER,
            spaceAfter=15,
            leading=26
        )
    
    def _get_body_style(self) -> ParagraphStyle:
        """Get body paragraph style"""
        return ParagraphStyle(
            name='PDFBody',
            fontName=self.FONTS['body'],
            fontSize=self._get_font_size('body', 14),
            textColor=self.text_color,
            alignment=TA_LEFT,
            spaceAfter=10,
            leftIndent=20,
            leading=18
        )
    
    def _get_bullet_style(self) -> ParagraphStyle:
        """Get bullet point style"""
        return ParagraphStyle(
            name='PDFBullet',
            fontName=self.FONTS['body'],
            fontSize=self._get_font_size('body', 14),
            textColor=self.text_color,
            alignment=TA_LEFT,
            spaceAfter=8,
            leftIndent=40,
            leading=18
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean text for PDF rendering"""
        if not text:
            return ""
        # Remove or escape special characters
        text = str(text)
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text
    
    def _create_slide_elements(self, slide: Dict) -> List:
        """Create PDF elements for a slide"""
        elements = []
        layout = slide.get('layout', 'content')
        
        # Top spacing
        elements.append(Spacer(1, 0.2*inch))
        
        # Route to layout handler
        handlers = {
            'title': self._create_title_slide,
            'content': self._create_content_slide,
            'two_column': self._create_two_column_slide,
            'chart': self._create_chart_slide,
            'table': self._create_table_slide,
            'quote': self._create_quote_slide,
            'metrics': self._create_metrics_slide,
            'timeline': self._create_timeline_slide,
            'comparison': self._create_comparison_slide,
            'conclusion': self._create_conclusion_slide,
            'image': self._create_image_slide
        }
        
        handler = handlers.get(layout, self._create_content_slide)
        elements.extend(handler(slide))
        
        return elements
    
    def _create_title_slide(self, slide: Dict) -> List:
        """Create title slide"""
        elements = []
        
        elements.append(Spacer(1, 1.5*inch))
        
        # Title
        title = self._clean_text(slide.get('title', 'Presentation'))
        elements.append(Paragraph(title, self._get_title_style()))
        
        # Decorative line
        elements.append(Spacer(1, 0.2*inch))
        line_table = Table([['']], colWidths=[3*inch], rowHeights=[3])
        line_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.accent_color),
        ]))
        elements.append(line_table)
        
        # Subtitle
        subtitle = self._clean_text(slide.get('subtitle', ''))
        if subtitle:
            elements.append(Spacer(1, 0.3*inch))
            elements.append(Paragraph(subtitle, self._get_subtitle_style()))
        
        return elements
    
    def _create_content_slide(self, slide: Dict) -> List:
        """Create content slide with bullets"""
        elements = []
        
        # Title
        title = self._clean_text(slide.get('title', ''))
        if title:
            elements.append(Paragraph(title, self._get_title_style()))
            elements.append(Spacer(1, 0.2*inch))
        
        # Content
        content_data = slide.get('content', {})
        
        # Bullet points
        bullets = content_data.get('bullet_points', [])
        for bullet in bullets:
            bullet_text = self._clean_text(bullet)
            elements.append(Paragraph(f"• {bullet_text}", self._get_bullet_style()))
        
        # Main text
        main_text = content_data.get('main_text', '')
        if main_text:
            elements.append(Paragraph(self._clean_text(main_text), self._get_body_style()))
        
        return elements
    
    def _create_two_column_slide(self, slide: Dict) -> List:
        """Create two-column slide"""
        elements = []
        
        # Title
        title = self._clean_text(slide.get('title', ''))
        if title:
            elements.append(Paragraph(title, self._get_title_style()))
            elements.append(Spacer(1, 0.2*inch))
        
        content_data = slide.get('content', {})
        
        # Build left column
        left_content = content_data.get('left_column', [])
        left_paras = []
        if isinstance(left_content, list):
            for item in left_content:
                left_paras.append(Paragraph(f"• {self._clean_text(item)}", self._get_bullet_style()))
        elif left_content:
            left_paras.append(Paragraph(self._clean_text(str(left_content)), self._get_body_style()))
        
        # Build right column
        right_content = content_data.get('right_column', [])
        right_paras = []
        if isinstance(right_content, list):
            for item in right_content:
                right_paras.append(Paragraph(f"• {self._clean_text(item)}", self._get_bullet_style()))
        elif right_content:
            right_paras.append(Paragraph(self._clean_text(str(right_content)), self._get_body_style()))
        
        # Create two-column table
        if left_paras or right_paras:
            col_table = Table(
                [[left_paras, right_paras]],
                colWidths=[4*inch, 4*inch]
            )
            col_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ]))
            elements.append(col_table)
        
        return elements
    
    def _create_chart_slide(self, slide: Dict) -> List:
        """Create chart slide (placeholder)"""
        elements = []
        
        # Title
        title = self._clean_text(slide.get('title', ''))
        if title:
            elements.append(Paragraph(title, self._get_title_style()))
            elements.append(Spacer(1, 0.3*inch))
        
        # Chart placeholder
        content_data = slide.get('content', {})
        chart_info = content_data.get('chart', {})
        chart_title = chart_info.get('title', 'Chart')
        chart_type = chart_info.get('type', 'bar')
        
        # Create chart representation table
        chart_box = Table(
            [[f"📊 {chart_type.upper()} CHART: {self._clean_text(chart_title)}"]],
            colWidths=[7*inch],
            rowHeights=[2*inch]
        )
        chart_box.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), self.FONTS['bold']),
            ('FONTSIZE', (0, 0), (-1, -1), 16),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.accent_color),
            ('BOX', (0, 0), (-1, -1), 2, self.accent_color),
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.95, 0.95, 0.98)),
        ]))
        elements.append(chart_box)
        
        # Chart data if available
        labels = chart_info.get('labels', [])
        if labels:
            elements.append(Spacer(1, 0.2*inch))
            labels_text = ", ".join([str(l) for l in labels])
            elements.append(Paragraph(f"Data: {labels_text}", self._get_body_style()))
        
        return elements
    
    def _create_table_slide(self, slide: Dict) -> List:
        """Create table slide"""
        elements = []
        
        # Title
        title = self._clean_text(slide.get('title', ''))
        if title:
            elements.append(Paragraph(title, self._get_title_style()))
            elements.append(Spacer(1, 0.2*inch))
        
        content_data = slide.get('content', {})
        table_info = content_data.get('table', {})
        
        headers = table_info.get('headers', [])
        rows = table_info.get('rows', [])
        
        if headers:
            # Build table data
            table_data = [[self._clean_text(h) for h in headers]]
            for row in rows:
                table_data.append([self._clean_text(str(cell)) for cell in row])
            
            # Calculate column widths
            num_cols = len(headers)
            col_width = 7.5*inch / num_cols
            
            # Create table
            pdf_table = Table(table_data, colWidths=[col_width] * num_cols)
            
            # Style
            style = [
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), self.accent_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), self.FONTS['bold']),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                # Data rows
                ('FONTNAME', (0, 1), (-1, -1), self.FONTS['body']),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('TEXTCOLOR', (0, 1), (-1, -1), self.text_color),
                # Grid
                ('GRID', (0, 0), (-1, -1), 1, colors.Color(0.7, 0.7, 0.7)),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]
            
            # Alternate row colors
            for i in range(1, len(table_data)):
                if i % 2 == 0:
                    style.append(('BACKGROUND', (0, i), (-1, i), colors.Color(0.95, 0.95, 0.95)))
                else:
                    style.append(('BACKGROUND', (0, i), (-1, i), colors.white))
            
            pdf_table.setStyle(TableStyle(style))
            elements.append(pdf_table)
        
        return elements
    
    def _create_quote_slide(self, slide: Dict) -> List:
        """Create quote slide"""
        elements = []
        
        content_data = slide.get('content', {})
        quote = self._clean_text(content_data.get('quote', ''))
        author = self._clean_text(content_data.get('quote_author', ''))
        
        elements.append(Spacer(1, 1.2*inch))
        
        # Quote style
        quote_style = ParagraphStyle(
            name='Quote',
            fontName=self.FONTS['italic'],
            fontSize=24,
            textColor=self.text_color,
            alignment=TA_CENTER,
            spaceAfter=20,
            leading=32,
            leftIndent=40,
            rightIndent=40
        )
        
        # Quote with marks
        elements.append(Paragraph(f'"{quote}"', quote_style))
        
        # Author
        if author:
            author_style = ParagraphStyle(
                name='Author',
                fontName=self.FONTS['body'],
                fontSize=16,
                textColor=self.secondary_color,
                alignment=TA_RIGHT,
                rightIndent=60
            )
            elements.append(Spacer(1, 0.3*inch))
            elements.append(Paragraph(f"— {author}", author_style))
        
        return elements
    
    def _create_metrics_slide(self, slide: Dict) -> List:
        """Create metrics/KPI slide"""
        elements = []
        
        # Title
        title = self._clean_text(slide.get('title', 'Key Metrics'))
        elements.append(Paragraph(title, self._get_title_style()))
        elements.append(Spacer(1, 0.4*inch))
        
        content_data = slide.get('content', {})
        metrics = content_data.get('key_metrics', [])
        
        if metrics:
            # Build metrics table
            values = []
            labels = []
            
            for metric in metrics[:4]:
                values.append(Paragraph(
                    f"<b>{self._clean_text(str(metric.get('value', '')))}</b>",
                    ParagraphStyle(
                        name='MetricValue',
                        fontName=self.FONTS['bold'],
                        fontSize=32,
                        textColor=self.highlight_color,
                        alignment=TA_CENTER
                    )
                ))
                labels.append(Paragraph(
                    self._clean_text(metric.get('label', '')),
                    ParagraphStyle(
                        name='MetricLabel',
                        fontName=self.FONTS['body'],
                        fontSize=12,
                        textColor=self.secondary_color,
                        alignment=TA_CENTER
                    )
                ))
            
            # Create table
            col_width = 7*inch / len(metrics[:4])
            metric_table = Table(
                [values, labels],
                colWidths=[col_width] * len(metrics[:4])
            )
            metric_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 20),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
            ]))
            elements.append(metric_table)
        
        return elements
    
    def _create_timeline_slide(self, slide: Dict) -> List:
        """Create timeline slide"""
        elements = []
        
        # Title
        title = self._clean_text(slide.get('title', 'Timeline'))
        elements.append(Paragraph(title, self._get_title_style()))
        elements.append(Spacer(1, 0.3*inch))
        
        content_data = slide.get('content', {})
        items = content_data.get('timeline_items', [])
        
        if items:
            # Build timeline table
            for item in items[:6]:
                date = self._clean_text(item.get('date', ''))
                event = self._clean_text(item.get('event', ''))
                
                row_table = Table(
                    [[Paragraph(f"<b>{date}</b>", ParagraphStyle(
                        name='TimelineDate',
                        fontName=self.FONTS['bold'],
                        fontSize=14,
                        textColor=self.accent_color
                    )),
                    Paragraph(event, self._get_body_style())]],
                    colWidths=[2*inch, 5.5*inch]
                )
                row_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ]))
                elements.append(row_table)
                elements.append(Spacer(1, 0.15*inch))
        
        return elements
    
    def _create_comparison_slide(self, slide: Dict) -> List:
        """Create comparison slide"""
        elements = []
        
        # Title
        title = self._clean_text(slide.get('title', 'Comparison'))
        elements.append(Paragraph(title, self._get_title_style()))
        elements.append(Spacer(1, 0.3*inch))
        
        content_data = slide.get('content', {})
        items = content_data.get('comparison_items', [])
        
        if len(items) >= 2:
            # Build comparison columns
            left_paras = []
            right_paras = []
            
            # Left item
            item1 = items[0]
            left_paras.append(Paragraph(
                f"<b>{self._clean_text(item1.get('title', 'Option 1'))}</b>",
                ParagraphStyle(name='CompTitle', fontName=self.FONTS['bold'], fontSize=18, 
                              textColor=self.accent_color, alignment=TA_CENTER, spaceAfter=10)
            ))
            for pro in item1.get('pros', []):
                left_paras.append(Paragraph(f"✓ {self._clean_text(pro)}", 
                    ParagraphStyle(name='Pro', fontName=self.FONTS['body'], fontSize=12, 
                                  textColor=colors.Color(0, 0.5, 0), leftIndent=10)))
            for con in item1.get('cons', []):
                left_paras.append(Paragraph(f"✗ {self._clean_text(con)}", 
                    ParagraphStyle(name='Con', fontName=self.FONTS['body'], fontSize=12, 
                                  textColor=colors.Color(0.7, 0, 0), leftIndent=10)))
            
            # Right item
            item2 = items[1]
            right_paras.append(Paragraph(
                f"<b>{self._clean_text(item2.get('title', 'Option 2'))}</b>",
                ParagraphStyle(name='CompTitle2', fontName=self.FONTS['bold'], fontSize=18, 
                              textColor=self.accent_color, alignment=TA_CENTER, spaceAfter=10)
            ))
            for pro in item2.get('pros', []):
                right_paras.append(Paragraph(f"✓ {self._clean_text(pro)}", 
                    ParagraphStyle(name='Pro2', fontName=self.FONTS['body'], fontSize=12, 
                                  textColor=colors.Color(0, 0.5, 0), leftIndent=10)))
            for con in item2.get('cons', []):
                right_paras.append(Paragraph(f"✗ {self._clean_text(con)}", 
                    ParagraphStyle(name='Con2', fontName=self.FONTS['body'], fontSize=12, 
                                  textColor=colors.Color(0.7, 0, 0), leftIndent=10)))
            
            # Create table
            comp_table = Table(
                [[left_paras, 
                  Paragraph("VS", ParagraphStyle(name='VS', fontName=self.FONTS['bold'], fontSize=24, 
                                                 textColor=self.highlight_color, alignment=TA_CENTER)),
                  right_paras]],
                colWidths=[3.2*inch, 0.6*inch, 3.2*inch]
            )
            comp_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ]))
            elements.append(comp_table)
        
        return elements
    
    def _create_conclusion_slide(self, slide: Dict) -> List:
        """Create conclusion slide"""
        elements = []
        
        elements.append(Spacer(1, 1*inch))
        
        # Title
        title = self._clean_text(slide.get('title', 'Thank You'))
        elements.append(Paragraph(title, self._get_title_style()))
        
        # Decorative line
        elements.append(Spacer(1, 0.2*inch))
        line_table = Table([['']], colWidths=[2*inch], rowHeights=[3])
        line_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.accent_color),
        ]))
        elements.append(line_table)
        
        elements.append(Spacer(1, 0.3*inch))
        
        # Bullet points
        content_data = slide.get('content', {})
        bullets = content_data.get('bullet_points', [])
        
        centered_style = ParagraphStyle(
            name='CenteredBullet',
            fontName=self.FONTS['body'],
            fontSize=self._get_font_size('body', 14),
            textColor=self.text_color,
            alignment=TA_CENTER,
            spaceAfter=8
        )
        
        for bullet in bullets:
            elements.append(Paragraph(f"• {self._clean_text(bullet)}", centered_style))
        
        # Call to action
        cta = content_data.get('call_to_action', '')
        if cta:
            elements.append(Spacer(1, 0.3*inch))
            cta_style = ParagraphStyle(
                name='CTA',
                fontName=self.FONTS['bold'],
                fontSize=16,
                textColor=self.highlight_color,
                alignment=TA_CENTER
            )
            elements.append(Paragraph(self._clean_text(cta), cta_style))
        
        return elements
    
    def _create_image_slide(self, slide: Dict) -> List:
        """Create image placeholder slide"""
        elements = []
        
        # Title
        title = self._clean_text(slide.get('title', ''))
        if title:
            elements.append(Paragraph(title, self._get_title_style()))
            elements.append(Spacer(1, 0.3*inch))
        
        content_data = slide.get('content', {})
        image_desc = self._clean_text(content_data.get('image_description', 'Image'))
        
        # Image placeholder
        img_box = Table(
            [[f"🖼️ IMAGE: {image_desc}"]],
            colWidths=[7*inch],
            rowHeights=[3*inch]
        )
        img_box.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), self.FONTS['body']),
            ('FONTSIZE', (0, 0), (-1, -1), 18),
            ('TEXTCOLOR', (0, 0), (-1, -1), self.secondary_color),
            ('BOX', (0, 0), (-1, -1), 2, self.secondary_color),
            ('BACKGROUND', (0, 0), (-1, -1), colors.Color(0.95, 0.95, 0.95)),
        ]))
        elements.append(img_box)
        
        return elements
