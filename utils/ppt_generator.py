"""Enhanced PowerPoint Generator - All bugs fixed"""
from pathlib import Path
import io
import base64
import logging
import re
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

logger = logging.getLogger(__name__)


class EnhancedPPTGenerator:

    LAYOUT_MAP = {
        'title': 0,
        'content': 1,
        'two_column': 1,
        'chart': 1,
        'table': 1,
        'quote': 1,
        'metrics': 1,
        'timeline': 1,
        'comparison': 1,
        'conclusion': 1,
        'image': 1
    }

    def __init__(self, template_path=None):
        if template_path:
            try:
                if Path(template_path).exists():
                    self.prs = Presentation(template_path)
                    logger.info(f"Template loaded: {template_path}")
                else:
                    logger.warning(f"Template not found: {template_path}")
                    self.prs = Presentation()
            except Exception as e:
                logger.error(f"Failed to load template: {e}")
                self.prs = Presentation()
        else:
            self.prs = Presentation()
        self.slide_width = self.prs.slide_width
        self.slide_height = self.prs.slide_height

    def generate(self, slides_data):
        for slide_data in slides_data:
            try:
                self._create_slide(slide_data)
            except Exception as e:
                logger.error(f"Slide {slide_data.get('slide_number')} failed: {e}", exc_info=True)
                self._create_error_slide(
                    slide_data.get('slide_number', '?'),
                    slide_data.get('layout', '?'),
                    str(e)
                )
        output = io.BytesIO()
        self.prs.save(output)
        output.seek(0)
        return output

    def _create_slide(self, slide_data):
        layout_type = slide_data.get('layout', 'content')
        layout_idx = self.LAYOUT_MAP.get(layout_type, 1)
        if layout_idx >= len(self.prs.slide_layouts):
            layout_idx = 1
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[layout_idx])
        if slide_data.get('title') and slide.shapes.title:
            slide.shapes.title.text = slide_data['title']
        handler = getattr(self, f'_handle_{layout_type}_layout', self._handle_content_layout)
        handler(slide, slide_data)

    def _handle_title_layout(self, slide, slide_data):
        content = slide_data.get('content', {})
        if slide.shapes.title:
            slide.shapes.title.text = slide_data.get('title', '')
        if len(slide.placeholders) > 1:
            slide.placeholders[1].text = slide_data.get('subtitle', content.get('subtitle', ''))

    def _handle_content_layout(self, slide, slide_data):
        content = slide_data.get('content', {})
        if len(slide.shapes) > 1 and slide.shapes[1].has_text_frame:
            tf = slide.shapes[1].text_frame
            tf.clear()
            if content.get('main_text'):
                p = tf.paragraphs[0]
                p.text = content['main_text']
                p.font.size = Pt(18)
            for bullet in content.get('bullet_points', []):
                p = tf.add_paragraph()
                p.text = f"- {bullet}"
                p.font.size = Pt(16)
            if slide_data.get('speaker_notes'):
                notes = slide_data['speaker_notes']
                if isinstance(notes, dict):
                    notes = str(notes)
                elif isinstance(notes, list):
                    notes = "\n".join([str(n) for n in notes])
                slide.notes_slide.notes_text_frame.text = str(notes)

    def _handle_two_column_layout(self, slide, slide_data):
        content = slide_data.get('content', {})
        if len(slide.shapes) > 1:
            slide.shapes._spTree.remove(slide.shapes[1]._element)
        top = Inches(2.0)
        bottom = Inches(0.5)
        margin = Inches(0.5)
        col_w = (self.slide_width - 2*margin - Inches(0.3)) / 2

        def add_col(left_pos, items):
            tb = slide.shapes.add_textbox(left_pos, top, col_w, self.slide_height - top - bottom)
            tf = tb.text_frame
            tf.word_wrap = True
            item_list = items if isinstance(items, list) else [items]
            for i, item in enumerate(item_list):
                p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                p.text = f"- {item}"
                p.font.size = Pt(14)

        add_col(margin, content.get('left_column', []) or [])
        add_col(margin + col_w + Inches(0.3), content.get('right_column', []) or [])

    def _handle_chart_layout(self, slide, slide_data):
        content = slide_data.get('content', {})
        chart = content.get('chart', {})
        if not chart:
            return self._handle_content_layout(slide, slide_data)
        if len(slide.shapes) > 1:
            slide.shapes._spTree.remove(slide.shapes[1]._element)
        w = self.slide_width * 0.8
        h = self.slide_height * 0.55
        shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, (self.slide_width-w)/2, Inches(2.0), w, h)
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(240, 240, 240)
        tf = shape.text_frame
        tf.text = f"Chart: {chart.get('title', 'Chart')}"
        tf.paragraphs[0].font.size = Pt(16)
        tf.paragraphs[0].font.bold = True
        if chart.get('description'):
            tf.add_paragraph().text = f"\n{chart['description']}"
        if chart.get('data'):
            info = slide.shapes.add_textbox(Inches(0.5), Inches(2.0)+h+Inches(0.2), self.slide_width-Inches(1), Inches(1.5))
            tf2 = info.text_frame
            tf2.paragraphs[0].text = "Data:"
            tf2.paragraphs[0].font.bold = True
            for k, v in chart['data'].items():
                tf2.add_paragraph().text = f"  - {k}: {v}"

    def _handle_table_layout(self, slide, slide_data):
        content = slide_data.get('content', {})
        table = content.get('table', {})
        if not table or not isinstance(table, dict):
            return self._handle_content_layout(slide, slide_data)
        headers = table.get('headers', [])
        data = table.get('data', [])
        if not headers or not isinstance(headers, list) or not data or not isinstance(data, list):
            return self._handle_content_layout(slide, slide_data)
        if len(slide.shapes) > 1:
            slide.shapes._spTree.remove(slide.shapes[1]._element)
        rows = len(data) + 1
        cols = len(headers)
        if cols == 0:
            return
        tw = self.slide_width * 0.9
        th = self.slide_height * 0.6
        ppt_table = slide.shapes.add_table(rows, cols, (self.slide_width-tw)/2, Inches(1.8), tw, th).table
        col_width = int(tw / cols)
        for i in range(cols):
            ppt_table.columns[i].width = col_width
        for i, h in enumerate(headers):
            c = ppt_table.cell(0, i)
            c.text = str(h)
            c.text_frame.paragraphs[0].font.bold = True
            c.text_frame.paragraphs[0].font.size = Pt(12)
        for ri, row in enumerate(data, 1):
            if not isinstance(row, (list, tuple)):
                row = [row]
            for ci, val in enumerate(row):
                if ci < cols:
                    c = ppt_table.cell(ri, ci)
                    c.text = str(val) if val is not None else ""
                    c.text_frame.paragraphs[0].font.size = Pt(10)

    def _handle_quote_layout(self, slide, slide_data):
        content = slide_data.get('content', {})
        if len(slide.shapes) > 1:
            slide.shapes._spTree.remove(slide.shapes[1]._element)
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(2.2), self.slide_width-Inches(1.6), Inches(2.5))
        tb.fill.solid()
        tb.fill.fore_color.rgb = RGBColor(245, 245, 245)
        tb.line.color.rgb = RGBColor(200, 200, 200)
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = '"' + content.get('quote', 'Quote text') + '"'
        p.font.size = Pt(20)
        p.font.italic = True
        if content.get('quote_author'):
            pa = tf.add_paragraph()
            pa.text = f"- {content['quote_author']}"
            pa.font.size = Pt(14)
            pa.alignment = PP_ALIGN.RIGHT

    def _handle_metrics_layout(self, slide, slide_data):
        content = slide_data.get('content', {})
        metrics = content.get('key_metrics', [])
        if not metrics:
            return self._handle_content_layout(slide, slide_data)
        if len(slide.shapes) > 1:
            slide.shapes._spTree.remove(slide.shapes[1]._element)
        n = len(metrics)
        bw = (self.slide_width - Inches(1)) / n - Inches(0.2)
        bh = Inches(2.5)
        top = Inches(2.2)
        left = Inches(0.5)
        for i, m in enumerate(metrics):
            box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left + i*(bw+Inches(0.2)), top, bw, bh)
            box.fill.solid()
            box.fill.fore_color.rgb = RGBColor(79, 129, 189)
            tf = box.text_frame
            tf.clear()
            pv = tf.paragraphs[0]
            pv.text = m.get('value', 'N/A')
            pv.font.size = Pt(28)
            pv.font.bold = True
            pv.alignment = PP_ALIGN.CENTER
            pl = tf.add_paragraph()
            pl.text = m.get('label', '')
            pl.font.size = Pt(14)
            pl.alignment = PP_ALIGN.CENTER

    def _handle_timeline_layout(self, slide, slide_data):
        content = slide_data.get('content', {})
        items = content.get('timeline_items', [])
        if not items:
            return self._handle_content_layout(slide, slide_data)
        if len(slide.shapes) > 1:
            slide.shapes._spTree.remove(slide.shapes[1]._element)
        tw = self.slide_width * 0.9
        tl = (self.slide_width - tw) / 2
        ty = Inches(3.0)
        line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, tl, ty+Inches(0.5), tw, Inches(0.05))
        line.fill.solid()
        line.fill.fore_color.rgb = RGBColor(79, 129, 189)
        line.line.fill.background()
        spacing = tw / max(len(items), 1)
        for i, it in enumerate(items):
            xp = tl + i*spacing + spacing/2
            mk = slide.shapes.add_shape(MSO_SHAPE.OVAL, xp-Inches(0.25), ty+Inches(0.3), Inches(0.5), Inches(0.5))
            mk.fill.solid()
            mk.fill.fore_color.rgb = RGBColor(79, 129, 189)
            tb = slide.shapes.add_textbox(xp-Inches(1), ty-Inches(0.8), Inches(2), Inches(0.6))
            p = tb.text_frame.paragraphs[0]
            p.text = it.get('date', '')
            p.font.bold = True
            p.font.size = Pt(12)
            p.alignment = PP_ALIGN.CENTER
            if it.get('description'):
                db = slide.shapes.add_textbox(xp-Inches(1.5), ty+Inches(1.0), Inches(3), Inches(1.5))
                dp = db.text_frame.paragraphs[0]
                dp.text = it['description']
                dp.font.size = Pt(10)
                dp.alignment = PP_ALIGN.CENTER

    def _handle_image_layout(self, slide, slide_data):
        content = slide_data.get('content', {})
        img = content.get('image', '')
        if len(slide.shapes) > 1:
            slide.shapes._spTree.remove(slide.shapes[1]._element)
        iw = self.slide_width * 0.7
        ih = self.slide_height * 0.55
        lp = (self.slide_width - iw) / 2
        tp = Inches(1.8)
        if not img or not isinstance(img, str) or img.strip() == '':
            self._add_image_placeholder(slide, lp, tp, iw, ih, "No image provided")
            return
        try:
            if img.startswith('http://') or img.startswith('https://'):
                self._add_image_placeholder(slide, lp, tp, iw, ih, "URL images not supported")
                return
            if img.startswith('image'):
                m = re.search(r'image/\w+;base64,(.+)', img)
                if m:
                    slide.shapes.add_picture(io.BytesIO(base64.b64decode(m.group(1))), lp, tp, width=iw, height=ih)
                    return
                else:
                    raise ValueError("Invalid base64")
            elif Path(img).exists() and img.strip() != '':
                slide.shapes.add_picture(img, lp, tp, width=iw, height=ih)
                return
            else:
                raise ValueError("Image file not found")
        except Exception as e:
            logger.warning(f"Image placeholder: {e}")
            self._add_image_placeholder(slide, lp, tp, iw, ih, str(e))

    def _add_image_placeholder(self, slide, left, top, width, height, reason):
        ph = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        ph.fill.solid()
        ph.fill.fore_color.rgb = RGBColor(240, 240, 240)
        tf = ph.text_frame
        tf.text = f"Image Placeholder\n({reason})"
        tf.paragraphs[0].font.size = Pt(14)
        tf.paragraphs[0].alignment = PP_ALIGN.CENTER

    def _handle_conclusion_layout(self, slide, slide_data):
        content = slide_data.get('content', {})
        if len(slide.shapes) > 1:
            slide.shapes._spTree.remove(slide.shapes[1]._element)
        cb = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(2.0), self.slide_width-Inches(1), Inches(3.0))
        cb.fill.solid()
        cb.fill.fore_color.rgb = RGBColor(79, 129, 189)
        tf = cb.text_frame
        tf.word_wrap = True
        if content.get('main_text'):
            p = tf.paragraphs[0]
            p.text = content['main_text']
            p.font.size = Pt(24)
            p.font.bold = True
            p.alignment = PP_ALIGN.CENTER
        for b in content.get('bullet_points', []):
            p = tf.add_paragraph()
            p.text = f"- {b}"
            p.font.size = Pt(16)
            p.alignment = PP_ALIGN.CENTER

    def _create_error_slide(self, num, layout, err):
        idx = 1 if len(self.prs.slide_layouts) > 1 else 0
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[idx])
        if slide.shapes.title:
            slide.shapes.title.text = f"Slide {num} Failed"
        if len(slide.shapes) > 1:
            tf = slide.shapes[1].text_frame
            tf.text = f"Layout: {layout}\nError: {err}\nCheck logs."
            tf.paragraphs[0].font.size = Pt(14)
            tf.paragraphs[0].font.color.rgb = RGBColor(255, 0, 0)
