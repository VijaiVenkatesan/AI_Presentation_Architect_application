"""
PowerPoint Generator Module - Enhanced Version
Creates presentations that preserve template styling
"""

import io
import copy
from typing import Dict, List, Optional, Tuple
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from pptx.oxml import parse_xml

from .chart_generator import ChartGenerator


class PresentationGenerator:
    """Generates PowerPoint presentations with template preservation"""
    
    def __init__(self, template_data: Optional[Dict] = None):
        self.template_data = template_data or self._get_default_template()
        self.chart_generator = ChartGenerator(self._get_chart_colors())
        self.prs = None
    
    def _get_default_template(self) -> Dict:
        """Default template settings"""
        return {
            'colors': {
                'primary': '#6366F1',
                'secondary': '#8B5CF6',
                'accent': '#EC4899',
                'background': '#0F172A',
                'text_primary': '#F8FAFC',
                'text_secondary': '#94A3B8'
            },
            'fonts': {
                'title': {'name': 'Arial', 'size': 44, 'bold': True, 'color': '#F8FAFC'},
                'subtitle': {'name': 'Arial', 'size': 28, 'bold': False, 'color': '#94A3B8'},
                'body': {'name': 'Arial', 'size': 18, 'bold': False, 'color': '#F8FAFC'}
            },
            'slide_size': {'width': 13.333, 'height': 7.5},
            'has_logo': False,
            'logo_image': None,
            'logo_position': {'left': 0.3, 'top': 0.3, 'width': 1.5, 'height': 0.75},
            'background': {'type': 'solid', 'color': '#0F172A'},
            'use_template_file': False,
            'template_bytes': None
        }
    
    def _get_chart_colors(self) -> Dict:
        """Get colors for charts"""
        colors = self.template_data.get('colors', {})
        return {
            'colors': [
                colors.get('primary', '#6366F1'),
                colors.get('secondary', '#8B5CF6'),
                colors.get('accent', '#EC4899'),
                '#10B981', '#F59E0B', '#EF4444', '#06B6D4', '#84CC16'
            ]
        }
    
    def generate_presentation(
        self,
        content: Dict,
        custom_settings: Optional[Dict] = None
    ) -> io.BytesIO:
        """Generate a PowerPoint presentation"""
        
        # Apply custom settings
        if custom_settings:
            self._apply_custom_settings(custom_settings)
        
        # Create presentation - use template if available
        if self.template_data.get('use_template_file') and self.template_data.get('template_bytes'):
            # Use uploaded template as base
            template_stream = io.BytesIO(self.template_data['template_bytes'])
            self.prs = Presentation(template_stream)
            
            # Clear existing slides but keep masters
            self._clear_slides_keep_masters()
        else:
            # Create new presentation
            self.prs = Presentation()
            self.prs.slide_width = Inches(self.template_data['slide_size']['width'])
            self.prs.slide_height = Inches(self.template_data['slide_size']['height'])
        
        # Generate slides
        slides = content.get('slides', [])
        for slide_content in slides:
            self._create_slide(slide_content)
        
        # Save to BytesIO
        output = io.BytesIO()
        self.prs.save(output)
        output.seek(0)
        
        return output
    
    def _clear_slides_keep_masters(self):
        """Remove all slides but keep slide masters"""
        # Remove slides in reverse order
        slide_ids = [slide.slide_id for slide in self.prs.slides]
        for slide_id in reversed(slide_ids):
            rId = self.prs.part.get_rel_by_target(
                self.prs.slides.get(slide_id).part
            ).rId
            self.prs.part.drop_rel(rId)
            del self.prs.slides._sldIdLst[
                self.prs.slides._sldIdLst.index(
                    self.prs.slides._sldIdLst[slide_id]
                )
            ]
    
    def _apply_custom_settings(self, settings: Dict):
        """Apply custom settings"""
        if 'colors' in settings:
            for key, value in settings['colors'].items():
                if value:  # Only update non-empty values
                    self.template_data['colors'][key] = value
        
        if 'fonts' in settings:
            if 'title_size' in settings['fonts']:
                self.template_data['fonts']['title']['size'] = settings['fonts']['title_size']
            if 'body_size' in settings['fonts']:
                self.template_data['fonts']['body']['size'] = settings['fonts']['body_size']
            if 'font_family' in settings['fonts']:
                for font_type in self.template_data['fonts']:
                    self.template_data['fonts'][font_type]['name'] = settings['fonts']['font_family']
    
    def _create_slide(self, slide_content: Dict):
        """Create a single slide"""
        layout_type = slide_content.get('layout', 'content')
        
        # Try to use matching layout from template
        layout = self._get_best_layout(layout_type)
        slide = self.prs.slides.add_slide(layout)
        
        # Add background if not using template
        if not self.template_data.get('use_template_file'):
            self._add_background(slide)
        
        # Add logo if template has one
        if self.template_data.get('has_logo') and self.template_data.get('logo_image'):
            self._add_logo(slide)
        
        # Create content based on layout
        layout_creators = {
            'title': self._create_title_slide,
            'content': self._create_content_slide,
            'two_column': self._create_two_column_slide,
            'chart': self._create_chart_slide,
            'table': self._create_table_slide,
            'quote': self._create_quote_slide,
            'conclusion': self._create_conclusion_slide,
            'metrics': self._create_metrics_slide,
            'timeline': self._create_timeline_slide,
            'comparison': self._create_comparison_slide,
            'image': self._create_image_slide
        }
        
        creator = layout_creators.get(layout_type, self._create_content_slide)
        creator(slide, slide_content)
        
        # Add slide number
        self._add_slide_number(slide, slide_content.get('slide_number', 0))
    
    def _get_best_layout(self, layout_type: str):
        """Get the best matching layout from template"""
        layout_mapping = {
            'title': ['Title Slide', 'Title', 'title'],
            'content': ['Title and Content', 'Content', 'Title, Content'],
            'two_column': ['Two Content', 'Comparison', 'Two Column'],
            'chart': ['Title and Content', 'Content with Caption'],
            'table': ['Title and Content', 'Content'],
            'quote': ['Title Only', 'Blank'],
            'conclusion': ['Title Slide', 'Section Header'],
            'metrics': ['Title and Content', 'Content'],
            'timeline': ['Title and Content', 'Content'],
            'comparison': ['Comparison', 'Two Content'],
            'image': ['Picture with Caption', 'Content']
        }
        
        preferred_names = layout_mapping.get(layout_type, ['Title and Content'])
        
        # Search for matching layout
        for layout in self.prs.slide_layouts:
            for name in preferred_names:
                if name.lower() in layout.name.lower():
                    return layout
        
        # Fallback to blank layout or first available
        for layout in self.prs.slide_layouts:
            if 'blank' in layout.name.lower():
                return layout
        
        return self.prs.slide_layouts[0]
    
    def _add_background(self, slide):
        """Add background to slide"""
        bg_info = self.template_data.get('background', {})
        bg_type = bg_info.get('type', 'solid')
        
        if bg_type == 'solid':
            background = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                0, 0,
                Inches(self.template_data['slide_size']['width']),
                Inches(self.template_data['slide_size']['height'])
            )
            background.fill.solid()
            background.fill.fore_color.rgb = self._hex_to_rgb(
                bg_info.get('color', self.template_data['colors']['background'])
            )
            background.line.fill.background()
            
            # Send to back
            spTree = slide.shapes._spTree
            sp = background._element
            spTree.remove(sp)
            spTree.insert(2, sp)
    
    def _add_logo(self, slide):
        """Add logo to slide"""
        try:
            logo_bytes = self.template_data.get('logo_image')
            logo_pos = self.template_data.get('logo_position', {})
            
            if logo_bytes:
                logo_stream = io.BytesIO(logo_bytes)
                slide.shapes.add_picture(
                    logo_stream,
                    Inches(logo_pos.get('left', 0.3)),
                    Inches(logo_pos.get('top', 0.3)),
                    Inches(logo_pos.get('width', 1.5)),
                    Inches(logo_pos.get('height', 0.75))
                )
        except Exception as e:
            print(f"Error adding logo: {e}")
    
    def _create_title_slide(self, slide, content: Dict):
        """Create title slide"""
        # Try to use placeholders first
        title_set = False
        subtitle_set = False
        
        for shape in slide.shapes:
            if shape.is_placeholder:
                ph_type = str(shape.placeholder_format.type)
                
                if 'TITLE' in ph_type or 'CENTER_TITLE' in ph_type:
                    if shape.has_text_frame:
                        shape.text_frame.clear()
                        p = shape.text_frame.paragraphs[0]
                        p.text = content.get('title', 'Presentation Title')
                        self._apply_font_style(p, 'title')
                        title_set = True
                
                elif 'SUBTITLE' in ph_type:
                    if shape.has_text_frame and content.get('subtitle'):
                        shape.text_frame.clear()
                        p = shape.text_frame.paragraphs[0]
                        p.text = content.get('subtitle', '')
                        self._apply_font_style(p, 'subtitle')
                        subtitle_set = True
        
        # Fallback to manual placement if placeholders not found
        if not title_set:
            title_box = slide.shapes.add_textbox(
                Inches(0.5), Inches(2.5),
                Inches(self.template_data['slide_size']['width'] - 1),
                Inches(1.5)
            )
            frame = title_box.text_frame
            p = frame.paragraphs[0]
            p.text = content.get('title', 'Presentation Title')
            self._apply_font_style(p, 'title')
            p.alignment = PP_ALIGN.CENTER
        
        if not subtitle_set and content.get('subtitle'):
            subtitle_box = slide.shapes.add_textbox(
                Inches(0.5), Inches(4.2),
                Inches(self.template_data['slide_size']['width'] - 1),
                Inches(1)
            )
            frame = subtitle_box.text_frame
            p = frame.paragraphs[0]
            p.text = content.get('subtitle', '')
            self._apply_font_style(p, 'subtitle')
            p.alignment = PP_ALIGN.CENTER
        
        # Add decorative line
        if not self.template_data.get('use_template_file'):
            line = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(self.template_data['slide_size']['width']/2 - 1.5),
                Inches(4),
                Inches(3),
                Inches(0.05)
            )
            line.fill.solid()
            line.fill.fore_color.rgb = self._hex_to_rgb(
                self.template_data['colors']['primary']
            )
            line.line.fill.background()
    
    def _create_content_slide(self, slide, content: Dict):
        """Create content slide"""
        self._add_slide_title(slide, content.get('title', ''))
        
        content_data = content.get('content', {})
        
        if content_data.get('bullet_points'):
            self._add_bullet_points(
                slide,
                content_data['bullet_points'],
                Inches(0.75), Inches(1.8),
                Inches(self.template_data['slide_size']['width'] - 1.5),
                Inches(5)
            )
        elif content_data.get('main_text'):
            self._add_text_box(
                slide,
                content_data['main_text'],
                Inches(0.75), Inches(1.8),
                Inches(self.template_data['slide_size']['width'] - 1.5),
                Inches(5)
            )
    
    def _create_two_column_slide(self, slide, content: Dict):
        """Create two-column slide"""
        self._add_slide_title(slide, content.get('title', ''))
        
        content_data = content.get('content', {})
        slide_width = self.template_data['slide_size']['width']
        col_width = (slide_width - 1.5) / 2
        
        # Left column
        left_content = content_data.get('left_column', '')
        if isinstance(left_content, list):
            self._add_bullet_points(
                slide, left_content,
                Inches(0.5), Inches(1.8),
                Inches(col_width), Inches(5)
            )
        else:
            self._add_text_box(
                slide, str(left_content),
                Inches(0.5), Inches(1.8),
                Inches(col_width), Inches(5)
            )
        
        # Divider
        line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            Inches(slide_width / 2),
            Inches(1.8),
            Inches(0.02),
            Inches(4.5)
        )
        line.fill.solid()
        line.fill.fore_color.rgb = self._hex_to_rgb(
            self.template_data['colors']['secondary']
        )
        line.line.fill.background()
        
        # Right column
        right_content = content_data.get('right_column', '')
        if isinstance(right_content, list):
            self._add_bullet_points(
                slide, right_content,
                Inches(slide_width / 2 + 0.25), Inches(1.8),
                Inches(col_width), Inches(5)
            )
        else:
            self._add_text_box(
                slide, str(right_content),
                Inches(slide_width / 2 + 0.25), Inches(1.8),
                Inches(col_width), Inches(5)
            )
    
    def _create_chart_slide(self, slide, content: Dict):
        """Create chart slide"""
        self._add_slide_title(slide, content.get('title', ''))
        
        content_data = content.get('content', {})
        chart_info = content_data.get('chart', {})
        
        if chart_info:
            chart_type = chart_info.get('type', 'bar')
            chart_data = {
                'title': chart_info.get('title', ''),
                'labels': chart_info.get('labels', ['A', 'B', 'C', 'D']),
                'datasets': chart_info.get('datasets', [
                    {'name': 'Series 1', 'values': [65, 78, 90, 85]}
                ]),
                'x_axis_label': chart_info.get('x_axis_label', ''),
                'y_axis_label': chart_info.get('y_axis_label', '')
            }
            
            try:
                # Update chart generator colors to match template
                self.chart_generator = ChartGenerator(self._get_chart_colors())
                chart_image = self.chart_generator.create_chart(chart_type, chart_data, 900, 450)
                
                image_stream = io.BytesIO(chart_image)
                slide.shapes.add_picture(
                    image_stream,
                    Inches(1.5), Inches(1.8),
                    Inches(self.template_data['slide_size']['width'] - 3),
                    Inches(5)
                )
            except Exception as e:
                print(f"Chart error: {e}")
                self._add_text_box(
                    slide,
                    f"[Chart: {chart_info.get('title', 'Data')}]",
                    Inches(1.5), Inches(3),
                    Inches(10), Inches(2)
                )
    
    def _create_table_slide(self, slide, content: Dict):
        """Create table slide"""
        self._add_slide_title(slide, content.get('title', ''))
        
        content_data = content.get('content', {})
        table_info = content_data.get('table', {})
        
        headers = table_info.get('headers', ['Column 1', 'Column 2'])
        rows = table_info.get('rows', [['Data 1', 'Data 2']])
        
        num_cols = len(headers)
        num_rows = len(rows) + 1
        
        table_width = min(self.template_data['slide_size']['width'] - 3, num_cols * 2)
        
        table = slide.shapes.add_table(
            num_rows, num_cols,
            Inches(1.5), Inches(2),
            Inches(table_width),
            Inches(min(num_rows * 0.6, 4.5))
        ).table
        
        # Style header row
        for i, header in enumerate(headers):
            cell = table.cell(0, i)
            cell.text = str(header)
            cell.fill.solid()
            cell.fill.fore_color.rgb = self._hex_to_rgb(
                self.template_data['colors']['primary']
            )
            
            para = cell.text_frame.paragraphs[0]
            para.font.bold = True
            para.font.color.rgb = RGBColor(255, 255, 255)
            para.font.size = Pt(14)
            para.font.name = self.template_data['fonts']['body'].get('name', 'Arial')
            para.alignment = PP_ALIGN.CENTER
        
        # Data rows
        for row_idx, row_data in enumerate(rows):
            for col_idx, cell_data in enumerate(row_data):
                if col_idx < num_cols:
                    cell = table.cell(row_idx + 1, col_idx)
                    cell.text = str(cell_data)
                    
                    # Alternate row colors
                    cell.fill.solid()
                    if row_idx % 2 == 0:
                        cell.fill.fore_color.rgb = self._hex_to_rgb('#1E293B')
                    else:
                        bg_color = self.template_data['colors'].get('background', '#0F172A')
                        cell.fill.fore_color.rgb = self._hex_to_rgb(bg_color)
                    
                    para = cell.text_frame.paragraphs[0]
                    para.font.color.rgb = self._hex_to_rgb(
                        self.template_data['colors']['text_primary']
                    )
                    para.font.size = Pt(12)
                    para.font.name = self.template_data['fonts']['body'].get('name', 'Arial')
                    para.alignment = PP_ALIGN.CENTER
    
    def _create_quote_slide(self, slide, content: Dict):
        """Create quote slide"""
        content_data = content.get('content', {})
        quote = content_data.get('quote', 'Add your quote here')
        author = content_data.get('quote_author', '')
        
        # Quote mark
        quote_mark = slide.shapes.add_textbox(
            Inches(1), Inches(2),
            Inches(1), Inches(1)
        )
        frame = quote_mark.text_frame
        p = frame.paragraphs[0]
        p.text = '"'
        p.font.size = Pt(120)
        p.font.color.rgb = self._hex_to_rgb(self.template_data['colors']['primary'])
        
        # Quote text
        quote_box = slide.shapes.add_textbox(
            Inches(2), Inches(2.5),
            Inches(self.template_data['slide_size']['width'] - 4),
            Inches(3)
        )
        frame = quote_box.text_frame
        frame.word_wrap = True
        p = frame.paragraphs[0]
        p.text = quote
        p.font.size = Pt(28)
        p.font.italic = True
        p.font.color.rgb = self._hex_to_rgb(
            self.template_data['colors']['text_primary']
        )
        p.font.name = self.template_data['fonts']['body'].get('name', 'Arial')
        p.alignment = PP_ALIGN.CENTER
        
        # Author
        if author:
            author_box = slide.shapes.add_textbox(
                Inches(2), Inches(5.5),
                Inches(self.template_data['slide_size']['width'] - 4),
                Inches(0.5)
            )
            frame = author_box.text_frame
            p = frame.paragraphs[0]
            p.text = f"— {author}"
            p.font.size = Pt(20)
            p.font.color.rgb = self._hex_to_rgb(
                self.template_data['colors']['secondary']
            )
            p.font.name = self.template_data['fonts']['body'].get('name', 'Arial')
            p.alignment = PP_ALIGN.RIGHT
    
    def _create_conclusion_slide(self, slide, content: Dict):
        """Create conclusion slide"""
        # Title
        title_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(2),
            Inches(self.template_data['slide_size']['width'] - 1),
            Inches(1.5)
        )
        frame = title_box.text_frame
        p = frame.paragraphs[0]
        p.text = content.get('title', 'Thank You')
        self._apply_font_style(p, 'title')
        p.font.size = Pt(48)
        p.alignment = PP_ALIGN.CENTER
        
        content_data = content.get('content', {})
        bullet_points = content_data.get('bullet_points', [])
        
        if bullet_points:
            self._add_bullet_points(
                slide, bullet_points,
                Inches(2), Inches(3.5),
                Inches(self.template_data['slide_size']['width'] - 4),
                Inches(3),
                centered=True
            )
        
        # Call to action
        cta = content_data.get('call_to_action', '')
        if cta:
            cta_box = slide.shapes.add_textbox(
                Inches(0.5), Inches(6.5),
                Inches(self.template_data['slide_size']['width'] - 1),
                Inches(0.5)
            )
            frame = cta_box.text_frame
            p = frame.paragraphs[0]
            p.text = cta
            p.font.size = Pt(18)
            p.font.color.rgb = self._hex_to_rgb(
                self.template_data['colors']['accent']
            )
            p.font.name = self.template_data['fonts']['body'].get('name', 'Arial')
            p.alignment = PP_ALIGN.CENTER
    
    def _create_metrics_slide(self, slide, content: Dict):
        """Create metrics slide"""
        self._add_slide_title(slide, content.get('title', 'Key Metrics'))
        
        content_data = content.get('content', {})
        metrics = content_data.get('key_metrics', [])
        
        if metrics:
            num_metrics = min(len(metrics), 4)
            slide_width = self.template_data['slide_size']['width']
            metric_width = (slide_width - 3) / num_metrics
            
            for i, metric in enumerate(metrics[:4]):
                x_pos = 1.5 + (i * metric_width)
                
                # Box
                box = slide.shapes.add_shape(
                    MSO_SHAPE.ROUNDED_RECTANGLE,
                    Inches(x_pos), Inches(2.5),
                    Inches(metric_width - 0.3), Inches(3)
                )
                box.fill.solid()
                box.fill.fore_color.rgb = self._hex_to_rgb('#1E293B')
                box.line.color.rgb = self._hex_to_rgb(
                    self.template_data['colors']['primary']
                )
                
                # Value
                value_box = slide.shapes.add_textbox(
                    Inches(x_pos), Inches(3),
                    Inches(metric_width - 0.3), Inches(1)
                )
                frame = value_box.text_frame
                p = frame.paragraphs[0]
                p.text = str(metric.get('value', '0'))
                p.font.size = Pt(36)
                p.font.bold = True
                p.font.color.rgb = self._hex_to_rgb(
                    self.template_data['colors']['accent']
                )
                p.font.name = self.template_data['fonts']['title'].get('name', 'Arial')
                p.alignment = PP_ALIGN.CENTER
                
                # Label
                label_box = slide.shapes.add_textbox(
                    Inches(x_pos), Inches(4.2),
                    Inches(metric_width - 0.3), Inches(0.8)
                )
                frame = label_box.text_frame
                frame.word_wrap = True
                p = frame.paragraphs[0]
                p.text = metric.get('label', 'Metric')
                p.font.size = Pt(16)
                p.font.color.rgb = self._hex_to_rgb(
                    self.template_data['colors']['text_secondary']
                )
                p.font.name = self.template_data['fonts']['body'].get('name', 'Arial')
                p.alignment = PP_ALIGN.CENTER
    
    def _create_timeline_slide(self, slide, content: Dict):
        """Create timeline slide"""
        self._add_slide_title(slide, content.get('title', 'Timeline'))
        
        content_data = content.get('content', {})
        items = content_data.get('timeline_items', [])
        
        if items:
            slide_width = self.template_data['slide_size']['width']
            
            # Timeline line
            line = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(1), Inches(4),
                Inches(slide_width - 2), Inches(0.05)
            )
            line.fill.solid()
            line.fill.fore_color.rgb = self._hex_to_rgb(
                self.template_data['colors']['primary']
            )
            line.line.fill.background()
            
            # Items
            item_count = min(len(items), 6)
            item_width = (slide_width - 2) / item_count
            
            for i, item in enumerate(items[:6]):
                x_pos = 1 + (i * item_width)
                
                # Circle
                circle = slide.shapes.add_shape(
                    MSO_SHAPE.OVAL,
                    Inches(x_pos + item_width/2 - 0.15), Inches(3.85),
                    Inches(0.3), Inches(0.3)
                )
                circle.fill.solid()
                circle.fill.fore_color.rgb = self._hex_to_rgb(
                    self.template_data['colors']['accent']
                )
                circle.line.fill.background()
                
                # Date
                date_box = slide.shapes.add_textbox(
                    Inches(x_pos), Inches(2.5),
                    Inches(item_width), Inches(0.5)
                )
                frame = date_box.text_frame
                p = frame.paragraphs[0]
                p.text = item.get('date', '')
                p.font.size = Pt(14)
                p.font.bold = True
                p.font.color.rgb = self._hex_to_rgb(
                    self.template_data['colors']['secondary']
                )
                p.font.name = self.template_data['fonts']['body'].get('name', 'Arial')
                p.alignment = PP_ALIGN.CENTER
                
                # Event
                event_box = slide.shapes.add_textbox(
                    Inches(x_pos), Inches(4.3),
                    Inches(item_width), Inches(1.5)
                )
                frame = event_box.text_frame
                frame.word_wrap = True
                p = frame.paragraphs[0]
                p.text = item.get('event', '')
                p.font.size = Pt(12)
                p.font.color.rgb = self._hex_to_rgb(
                    self.template_data['colors']['text_primary']
                )
                p.font.name = self.template_data['fonts']['body'].get('name', 'Arial')
                p.alignment = PP_ALIGN.CENTER
    
    def _create_comparison_slide(self, slide, content: Dict):
        """Create comparison slide"""
        self._add_slide_title(slide, content.get('title', 'Comparison'))
        
        content_data = content.get('content', {})
        items = content_data.get('comparison_items', [])
        
        if len(items) >= 2:
            slide_width = self.template_data['slide_size']['width']
            box_width = (slide_width - 2) / 2 - 0.5
            
            for idx, item in enumerate(items[:2]):
                x_start = 0.5 if idx == 0 else slide_width/2 + 0.25
                
                # Box
                box = slide.shapes.add_shape(
                    MSO_SHAPE.ROUNDED_RECTANGLE,
                    Inches(x_start), Inches(1.8),
                    Inches(box_width), Inches(5)
                )
                box.fill.solid()
                box.fill.fore_color.rgb = self._hex_to_rgb('#1E293B')
                box.line.color.rgb = self._hex_to_rgb(
                    self.template_data['colors']['primary']
                )
                
                # Title
                title_box = slide.shapes.add_textbox(
                    Inches(x_start + 0.3), Inches(2),
                    Inches(box_width - 0.6), Inches(0.6)
                )
                frame = title_box.text_frame
                p = frame.paragraphs[0]
                p.text = item.get('title', f'Option {idx + 1}')
                p.font.size = Pt(24)
                p.font.bold = True
                p.font.color.rgb = self._hex_to_rgb(
                    self.template_data['colors']['text_primary']
                )
                p.font.name = self.template_data['fonts']['title'].get('name', 'Arial')
                p.alignment = PP_ALIGN.CENTER
                
                # Pros
                pros = item.get('pros', [])
                y_pos = 2.8
                for pro in pros[:3]:
                    pro_box = slide.shapes.add_textbox(
                        Inches(x_start + 0.3), Inches(y_pos),
                        Inches(box_width - 0.6), Inches(0.4)
                    )
                    frame = pro_box.text_frame
                    p = frame.paragraphs[0]
                    p.text = f"✓ {pro}"
                    p.font.size = Pt(14)
                    p.font.color.rgb = self._hex_to_rgb('#10B981')
                    p.font.name = self.template_data['fonts']['body'].get('name', 'Arial')
                    y_pos += 0.5
                
                # Cons
                cons = item.get('cons', [])
                y_pos = 4.8
                for con in cons[:3]:
                    con_box = slide.shapes.add_textbox(
                        Inches(x_start + 0.3), Inches(y_pos),
                        Inches(box_width - 0.6), Inches(0.4)
                    )
                    frame = con_box.text_frame
                    p = frame.paragraphs[0]
                    p.text = f"✗ {con}"
                    p.font.size = Pt(14)
                    p.font.color.rgb = self._hex_to_rgb('#EF4444')
                    p.font.name = self.template_data['fonts']['body'].get('name', 'Arial')
                    y_pos += 0.5
            
            # VS
            vs_box = slide.shapes.add_textbox(
                Inches(slide_width/2 - 0.5), Inches(3.5),
                Inches(1), Inches(1)
            )
            frame = vs_box.text_frame
            p = frame.paragraphs[0]
            p.text = "VS"
            p.font.size = Pt(36)
            p.font.bold = True
            p.font.color.rgb = self._hex_to_rgb(
                self.template_data['colors']['accent']
            )
            p.font.name = self.template_data['fonts']['title'].get('name', 'Arial')
            p.alignment = PP_ALIGN.CENTER
    
    def _create_image_slide(self, slide, content: Dict):
        """Create image placeholder slide"""
        self._add_slide_title(slide, content.get('title', ''))
        
        content_data = content.get('content', {})
        image_desc = content_data.get('image_description', 'Image Placeholder')
        
        slide_width = self.template_data['slide_size']['width']
        
        # Placeholder
        placeholder = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(1.5), Inches(1.8),
            Inches(slide_width - 3), Inches(5)
        )
        placeholder.fill.solid()
        placeholder.fill.fore_color.rgb = self._hex_to_rgb('#1E293B')
        placeholder.line.color.rgb = self._hex_to_rgb(
            self.template_data['colors']['secondary']
        )
        placeholder.line.width = Pt(2)
        
        # Description
        text_box = slide.shapes.add_textbox(
            Inches(1.5), Inches(4),
            Inches(slide_width - 3), Inches(1)
        )
        frame = text_box.text_frame
        p = frame.paragraphs[0]
        p.text = f"📷 {image_desc}"
        p.font.size = Pt(18)
        p.font.color.rgb = self._hex_to_rgb(
            self.template_data['colors']['text_secondary']
        )
        p.font.name = self.template_data['fonts']['body'].get('name', 'Arial')
        p.alignment = PP_ALIGN.CENTER
    
    def _add_slide_title(self, slide, title: str):
        """Add title to slide"""
        # Try to use placeholder first
        for shape in slide.shapes:
            if shape.is_placeholder:
                ph_type = str(shape.placeholder_format.type)
                if 'TITLE' in ph_type:
                    if shape.has_text_frame:
                        shape.text_frame.clear()
                        p = shape.text_frame.paragraphs[0]
                        p.text = title
                        self._apply_font_style(p, 'title')
                        return
        
        # Manual title
        title_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(0.4),
            Inches(self.template_data['slide_size']['width'] - 1),
            Inches(1)
        )
        frame = title_box.text_frame
        p = frame.paragraphs[0]
        p.text = title
        self._apply_font_style(p, 'title')
        
        # Underline (only if not using template)
        if not self.template_data.get('use_template_file'):
            line = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE,
                Inches(0.5), Inches(1.4),
                Inches(2), Inches(0.04)
            )
            line.fill.solid()
            line.fill.fore_color.rgb = self._hex_to_rgb(
                self.template_data['colors']['primary']
            )
            line.line.fill.background()
    
    def _add_bullet_points(
        self,
        slide,
        points: List[str],
        left, top, width, height,
        centered: bool = False
    ):
        """Add bullet points"""
        text_box = slide.shapes.add_textbox(left, top, width, height)
        frame = text_box.text_frame
        frame.word_wrap = True
        
        font_info = self.template_data['fonts']['body']
        
        for i, point in enumerate(points):
            if i == 0:
                p = frame.paragraphs[0]
            else:
                p = frame.add_paragraph()
            
            p.text = f"• {point}"
            p.font.size = Pt(font_info.get('size', 18))
            p.font.color.rgb = self._hex_to_rgb(
                font_info.get('color', self.template_data['colors']['text_primary'])
            )
            p.font.name = font_info.get('name', 'Arial')
            p.font.bold = font_info.get('bold', False)
            p.space_after = Pt(12)
            
            if centered:
                p.alignment = PP_ALIGN.CENTER
    
    def _add_text_box(self, slide, text: str, left, top, width, height):
        """Add text box"""
        text_box = slide.shapes.add_textbox(left, top, width, height)
        frame = text_box.text_frame
        frame.word_wrap = True
        
        font_info = self.template_data['fonts']['body']
        
        p = frame.paragraphs[0]
        p.text = text
        p.font.size = Pt(font_info.get('size', 18))
        p.font.color.rgb = self._hex_to_rgb(
            font_info.get('color', self.template_data['colors']['text_primary'])
        )
        p.font.name = font_info.get('name', 'Arial')
    
    def _add_slide_number(self, slide, number: int):
        """Add slide number"""
        if number <= 0:
            return
        
        slide_width = self.template_data['slide_size']['width']
        slide_height = self.template_data['slide_size']['height']
        
        num_box = slide.shapes.add_textbox(
            Inches(slide_width - 1),
            Inches(slide_height - 0.5),
            Inches(0.8),
            Inches(0.4)
        )
        frame = num_box.text_frame
        p = frame.paragraphs[0]
        p.text = str(number)
        p.font.size = Pt(12)
        p.font.color.rgb = self._hex_to_rgb(
            self.template_data['colors']['text_secondary']
        )
        p.font.name = self.template_data['fonts']['body'].get('name', 'Arial')
        p.alignment = PP_ALIGN.RIGHT
    
    def _apply_font_style(self, paragraph, style_name: str):
        """Apply font style to paragraph"""
        font_info = self.template_data['fonts'].get(style_name, {})
        
        paragraph.font.name = font_info.get('name', 'Arial')
        paragraph.font.size = Pt(font_info.get('size', 18))
        paragraph.font.bold = font_info.get('bold', False)
        paragraph.font.color.rgb = self._hex_to_rgb(
            font_info.get('color', self.template_data['colors']['text_primary'])
        )
    
    def _hex_to_rgb(self, hex_color: str) -> RGBColor:
        """Convert hex to RGBColor"""
        hex_color = hex_color.lstrip('#')
        return RGBColor(
            int(hex_color[0:2], 16),
            int(hex_color[2:4], 16),
            int(hex_color[4:6], 16)
        )
