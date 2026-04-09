"""
Enterprise AI Presentation Architect — Preview Engine
Renders slide previews as HTML cards for Streamlit display.
"""

import io
import logging
from typing import Dict, List, Optional

logger = logging.getLogger("PresentationArchitect")


class PreviewEngine:
    """
    Generates visual slide previews for the Streamlit UI.
    Renders slides as styled HTML cards with content representation.
    """

    # Color palette for slide backgrounds
    SLIDE_COLORS = [
        "#1a1a2e", "#16213e", "#0f3460", "#1b262c",
        "#2d3436", "#1e272e", "#2c3e50", "#34495e",
    ]

    def render_slide_preview(self, content: Dict, index: int, total: int) -> str:
        """Render a single slide as an HTML card."""
        title = content.get("title", f"Slide {index + 1}")
        subtitle = content.get("subtitle", "")
        bullets = content.get("bullet_points", [])
        chart = content.get("chart_data")
        table = content.get("table_data")
        notes = content.get("notes", "")
        slide_num = content.get("slide_number", index + 1)

        bg_color = self.SLIDE_COLORS[index % len(self.SLIDE_COLORS)]
        is_title_slide = (index == 0)

        # Build HTML
        html_parts = [f'''<div style="
            background: linear-gradient(135deg, {bg_color} 0%, {self._lighten(bg_color, 20)} 100%);
            border-radius: 12px; padding: 24px 28px; margin: 8px 0;
            color: white; min-height: 200px; position: relative;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            font-family: 'Segoe UI', Calibri, sans-serif;">''']

        # Slide number badge
        html_parts.append(f'''<div style="position:absolute; top:12px; right:16px;
            background:rgba(255,255,255,0.15); border-radius:20px;
            padding:3px 12px; font-size:11px; color:rgba(255,255,255,0.7);">
            {slide_num} / {total}</div>''')

        if is_title_slide:
            html_parts.append(self._render_title_slide(title, subtitle))
        else:
            html_parts.append(self._render_content_slide(title, bullets, chart, table))

        # Notes indicator
        if notes:
            html_parts.append(f'''<div style="position:absolute; bottom:8px; right:16px;
                font-size:10px; color:rgba(255,255,255,0.4);">📝 Has speaker notes</div>''')

        html_parts.append("</div>")
        return "".join(html_parts)

    def _render_title_slide(self, title: str, subtitle: str) -> str:
        parts = [f'''<div style="display:flex; flex-direction:column;
            justify-content:center; align-items:center; min-height:160px; text-align:center;">
            <h2 style="margin:0 0 12px 0; font-size:24px; font-weight:700;
            color:white; line-height:1.3;">{self._escape(title)}</h2>''']
        if subtitle:
            parts.append(f'''<p style="margin:0; font-size:14px;
                color:rgba(255,255,255,0.7); font-weight:300;">
                {self._escape(subtitle)}</p>''')
        parts.append("</div>")
        return "".join(parts)

    def _render_content_slide(self, title, bullets, chart, table) -> str:
        parts = [f'''<h3 style="margin:0 0 14px 0; font-size:17px; font-weight:600;
            color:white; border-bottom:2px solid rgba(255,255,255,0.2);
            padding-bottom:8px;">{self._escape(title)}</h3>''']

        if bullets:
            parts.append('<ul style="margin:0; padding-left:18px; list-style:none;">')
            for bp in bullets[:6]:
                parts.append(f'''<li style="margin:3px 0; font-size:12px;
                    color:rgba(255,255,255,0.85); line-height:1.5;">
                    <span style="color:#00d4ff; margin-right:6px;">▸</span>
                    {self._escape(bp)}</li>''')
            if len(bullets) > 6:
                parts.append(f'''<li style="font-size:11px; color:rgba(255,255,255,0.5);
                    margin-top:4px;">+{len(bullets)-6} more points...</li>''')
            parts.append("</ul>")

        if chart:
            ct = chart.get("type", "bar")
            icon = {"bar": "📊", "pie": "🥧", "line": "📈", "doughnut": "🍩"}.get(ct, "📊")
            parts.append(f'''<div style="margin-top:10px; background:rgba(255,255,255,0.08);
                border-radius:8px; padding:10px; text-align:center;">
                <span style="font-size:24px;">{icon}</span>
                <p style="margin:4px 0 0 0; font-size:11px; color:rgba(255,255,255,0.6);">
                {ct.title()} Chart: {self._escape(chart.get("title",""))}</p></div>''')

        if table:
            headers = table.get("headers", [])
            rows = table.get("rows", [])
            parts.append(f'''<div style="margin-top:10px; background:rgba(255,255,255,0.08);
                border-radius:8px; padding:10px; text-align:center;">
                <span style="font-size:24px;">📋</span>
                <p style="margin:4px 0 0 0; font-size:11px; color:rgba(255,255,255,0.6);">
                Table: {len(headers)} cols × {len(rows)} rows</p></div>''')

        return "".join(parts)

    def render_slide_thumbnail(self, content: Dict, index: int, selected: bool = False) -> str:
        """Render a small thumbnail for the slide navigator."""
        title = content.get("title", f"Slide {index+1}")
        short_title = title[:30] + "..." if len(title) > 30 else title
        border = "2px solid #00d4ff" if selected else "1px solid rgba(255,255,255,0.15)"
        bg = "rgba(0,123,255,0.15)" if selected else "rgba(255,255,255,0.05)"

        return f'''<div style="background:{bg}; border:{border}; border-radius:8px;
            padding:8px 10px; margin:4px 0; cursor:pointer; transition:all 0.2s;">
            <div style="font-size:10px; color:rgba(255,255,255,0.5);">Slide {index+1}</div>
            <div style="font-size:12px; color:white; font-weight:500; margin-top:2px;
            white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{self._escape(short_title)}</div>
        </div>'''

    def render_all_previews(self, slides: List[Dict]) -> List[str]:
        """Render previews for all slides."""
        total = len(slides)
        return [self.render_slide_preview(s, i, total) for i, s in enumerate(slides)]

    def _escape(self, text: str) -> str:
        if not text: return ""
        return text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

    def _lighten(self, hex_color: str, amount: int) -> str:
        try:
            h = hex_color.lstrip("#")
            r = min(255, int(h[0:2], 16) + amount)
            g = min(255, int(h[2:4], 16) + amount)
            b = min(255, int(h[4:6], 16) + amount)
            return f"#{r:02x}{g:02x}{b:02x}"
        except: return hex_color
