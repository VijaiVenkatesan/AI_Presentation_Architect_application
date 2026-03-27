"""Enhanced PDF Generator - Fixed syntax"""
from typing import Dict, List, Any, Optional
from pathlib import Path
import io, base64, re, logging
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.colors import HexColor, black, grey
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

logger = logging.getLogger(__name__)

class EnhancedPDFGenerator:
    def __init__(self, page_size=A4):
        self.page_size = page_size
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        self.styles.add(ParagraphStyle(
            name='Title', parent=self.styles['Heading1'], fontSize=24,
            textColor=HexColor('#4F81BD'), spaceAfter=20, alignment=TA_CENTER, fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='Content', parent=self.styles['Normal'], fontSize=12,
            spaceAfter=10, fontName='Helvetica'
        ))
        self.styles.add(ParagraphStyle(
            name='Bullet', parent=self.styles['Normal'], fontSize=11,
            leftIndent=20, spaceAfter=5, fontName='Helvetica'
        ))
        self.styles.add(ParagraphStyle(
            name='Quote', parent=self.styles['Normal'], fontSize=14,
            textColor=grey, leftIndent=40, rightIndent=40, spaceAfter=15,
            alignment=TA_JUSTIFY, fontName='Helvetica-Oblique'
        ))
        self.styles.add(ParagraphStyle(
            name='Metric', parent=self.styles['Normal'], fontSize=28,
            textColor=HexColor('#4F81BD'), alignment=TA_CENTER, fontName='Helvetica-Bold'
        ))
    
    def generate(self, slides_data: List[Dict[str, Any]], output_path: Optional[str] = None) -> io.BytesIO:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=self.page_size, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        story = []
        for sd in slides_data:
            try:
                story.extend(self._make_slide(sd))
                story.append(Spacer(1, 0.5*inch))
                story.append(PageBreak())
            except Exception as e:
                logger.error(f"PDF slide error: {e}")
                story.append(Paragraph(f"Slide {sd.get('slide_number')} Error", self.styles['Title']))
        doc.build(story)
        buf.seek(0)
        return buf
    
    def _make_slide(self, slide_data: Dict[str, Any]) -> List:
        elems = []
        layout = slide_data.get('layout', 'content')
        if slide_data.get('title'):
            elems.append(Paragraph(slide_data['title'], self.styles['Title']))
            elems.append(Spacer(1, 0.2*inch))
        handler = getattr(self, f'_pdf_{layout}', self._pdf_content)
        elems.extend(handler(slide_data))
        return elems
    
    def _pdf_content(self, sd: Dict[str, Any]) -> List:
        elems = []
        c = sd.get('content', {})
        if c.get('main_text'):
            elems.append(Paragraph(c['main_text'], self.styles['Content']))
            elems.append(Spacer(1, 0.1*inch))
        for b in c.get('bullet_points', []):
            elems.append(Paragraph(f"- {b}", self.styles['Bullet']))
        return elems
    
    def _pdf_two_column(self, sd: Dict[str, Any]) -> List:
        c = sd.get('content', {})
        lc = c.get('left_column', [])
        rc = c.get('right_column', [])
        if isinstance(lc, str): lc = [lc]
        if isinstance(rc, str): rc = [rc]
        td = [['\n'.join([f"- {x}" for x in lc]), '\n'.join([f"- {x}" for x in rc])]]
        t = Table(td, colWidths=[3.5*inch, 3.5*inch])
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),12)]))
        return [t]
    
    def _pdf_chart(self, sd: Dict[str, Any]) -> List:
        elems = []
        c = sd.get('content', {}).get('chart', {})
        if c.get('title'):
            elems.append(Paragraph(f"📊 {c['title']}", self.styles['Content']))
            elems.append(Spacer(1, 0.1*inch))
        if c.get('description'):
            elems.append(Paragraph(c['description'], self.styles['Content']))
            elems.append(Spacer(1, 0.1*inch))
        if c.get('data'):
            td = [['Metric','Value']] + [[k,str(v)] for k,v in c['data'].items()]
            t = Table(td, colWidths=[3*inch,3*inch])
            t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#4F81BD')),('GRID',(0,0),(-1,-1),1,black)]))
            elems.append(t)
        return elems
    
    def _pdf_table(self, sd: Dict[str, Any]) -> List:
        c = sd.get('content', {}).get('table', {})
        if not c or not c.get('headers'):
            return []
        data = [c['headers']] + c.get('data', [])
        t = Table(data, colWidths=[2*inch]*len(c['headers']))
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#4F81BD')),('GRID',(0,0),(-1,-1),1,black),('FONTSIZE',(0,0),(-1,-1),10)]))
        return [t]
    
    def _pdf_quote(self, sd: Dict[str, Any]) -> List:
        c = sd.get('content', {})
        elems = [Paragraph('"' + c.get('quote','') + '"', self.styles['Quote'])]
        if c.get('quote_author'):
            elems.append(Paragraph(f"- {c['quote_author']}", self.styles['Bullet']))
        return elems
    
    def _pdf_metrics(self, sd: Dict[str, Any]) -> List:
        metrics = sd.get('content', {}).get('key_metrics', [])
        if not metrics:
            return []
        td = [[Paragraph(m.get('value','N/A'), self.styles['Metric']), Paragraph(m.get('label',''), self.styles['Content'])] for m in metrics]
        t = Table(td, colWidths=[2.5*inch, 3.5*inch])
        t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(0,0),(0,-1),'CENTER')]))
        return [t]
    
    def _pdf_image(self, sd: Dict[str, Any]) -> List:
        img = sd.get('content', {}).get('image', '')
        if not img:
            return [Paragraph("🖼️ No image", self.styles['Content'])]
        try:
            if isinstance(img, str) and img.startswith('image'):
                m = re.search(r'image/\w+;base64,(.+)', img)
                if m:
                    return [Image(io.BytesIO(base64.b64decode(m.group(1))), width=5*inch, height=3.5*inch)]
        except:
            pass
        return [Paragraph("🖼️ Image placeholder", self.styles['Content'])]
    
    def _pdf_timeline(self, sd: Dict[str, Any]) -> List:
        elems = []
        for it in sd.get('content', {}).get('timeline_items', []):
            elems.append(Paragraph(f"📅 {it.get('date','')}", self.styles['Content']))
            elems.append(Paragraph(it.get('description',''), self.styles['Bullet']))
            elems.append(Spacer(1, 0.1*inch))
        return elems
    
    def _pdf_conclusion(self, sd: Dict[str, Any]) -> List:
        elems = []
        c = sd.get('content', {})
        if c.get('main_text'):
            elems.append(Paragraph(c['main_text'], self.styles['Title']))
            elems.append(Spacer(1, 0.1*inch))
        for b in c.get('bullet_points', []):
            elems.append(Paragraph(f"- {b}", self.styles['Bullet']))
        return elems
