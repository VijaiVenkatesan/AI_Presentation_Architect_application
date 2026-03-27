"""Preview Component - Fixed for dark mode visibility"""
import streamlit as st
from typing import Dict, List, Any


def render_slide_preview(slide_data: Dict[str, Any], idx: int):
    """Render a single slide preview - FIXED contrast"""
    layout = slide_data.get('layout', 'content')
    title = slide_data.get('title', '')
    content = slide_data.get('content', {})
    
    html = f'''<div style="background:#ffffff;border:2px solid #4F81BD;border-radius:8px;padding:40px;margin:20px 0;min-height:400px;box-shadow:0 4px 12px rgba(0,0,0,0.15);font-family:'Segoe UI',Arial,sans-serif;color:#1a1a1a">'''
    
    if title:
        html += f'''<h2 style="color:#4F81BD;font-size:28px;margin-bottom:20px;border-bottom:3px solid #4F81BD;padding-bottom:10px;font-weight:bold">{title}</h2>'''
    
    if layout == 'content':
        html += _render_content(content)
    elif layout == 'two_column':
        html += _render_two_col(content)
    elif layout == 'chart':
        html += _render_chart(content)
    elif layout == 'table':
        html += _render_table(content)
    elif layout == 'quote':
        html += _render_quote(content)
    elif layout == 'metrics':
        html += _render_metrics(content)
    elif layout == 'image':
        html += _render_image(content)
    elif layout == 'timeline':
        html += _render_timeline(content)
    elif layout == 'conclusion':
        html += _render_conclusion(content)
    else:
        html += _render_content(content)
    
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def display_all_slides_preview(slides_data: List[Dict[str, Any]]):
    """Display all slides in preview mode"""
    if not slides_data:
        st.info("No slides to preview")
        return
    for i, sd in enumerate(slides_data, 1):
        with st.expander(f"Slide {i} ({sd.get('layout','content')})", expanded=(i==1)):
            render_slide_preview(sd, i)


def _render_content(c: Dict[str, Any]) -> str:
    h = ""
    if c.get('main_text'):
        h += f"<p style='font-size:16px;margin-bottom:15px;color:#1a1a1a;line-height:1.6'>{c['main_text']}</p>"
    for b in c.get('bullet_points', []):
        h += f"<p style='font-size:14px;margin:8px 0;padding-left:20px;color:#2a2a2a'>• {b}</p>"
    return h


def _render_two_col(c: Dict[str, Any]) -> str:
    l = c.get('left_column', []) or []
    r = c.get('right_column', []) or []
    if isinstance(l, str):
        l = [l]
    if isinstance(r, str):
        r = [r]
    lh = "".join([f"<p style='margin:8px 0;color:#1a1a1a'>• {x}</p>" for x in l])
    rh = "".join([f"<p style='margin:8px 0;color:#1a1a1a'>• {x}</p>" for x in r])
    return f"<div style='display:flex;gap:30px'><div style='flex:1;background:#f8f9fa;padding:15px;border-radius:8px'>{lh}</div><div style='flex:1;background:#f8f9fa;padding:15px;border-radius:8px'>{rh}</div></div>"


def _render_chart(c: Dict[str, Any]) -> str:
    cd = c.get('chart', {}) or {}
    h = f"<h3 style='color:#4F81BD;font-size:20px'>📊 {cd.get('title','Chart')}</h3>"
    if cd.get('description'):
        h += f"<p style='font-size:14px;margin:10px 0;color:#333'>{cd['description']}</p>"
    if cd.get('data'):
        h += "<table style='width:100%;border-collapse:collapse;margin-top:15px;border:2px solid #4F81BD'>"
        h += "<tr style='background:#4F81BD;color:white'><th style='padding:12px;border:1px solid #4F81BD'>Metric</th><th style='padding:12px;border:1px solid #4F81BD'>Value</th></tr>"
        for k, v in cd['data'].items():
            h += f"<tr><td style='padding:10px;border:1px solid #ddd;color:#1a1a1a'>{k}</td><td style='padding:10px;border:1px solid #ddd;color:#1a1a1a'>{v}</td></tr>"
        h += "</table>"
    return h


def _render_table(c: Dict[str, Any]) -> str:
    td = c.get('table', {}) or {}
    if not td.get('headers'):
        return "<p style='color:#666'>No table data</p>"
    h = "<table style='width:100%;border-collapse:collapse;margin-top:15px;border:2px solid #4F81BD'>"
    h += "<tr style='background:#4F81BD;color:white'>"
    for hdr in td['headers']:
        h += f"<th style='padding:12px;border:1px solid #4F81BD'>{hdr}</th>"
    h += "</tr>"
    for row in td.get('data', []):
        h += "<tr>"
        for cell in row:
            h += f"<td style='padding:10px;border:1px solid #ddd;color:#1a1a1a;text-align:center'>{cell}</td>"
        h += "</tr>"
    h += "</table>"
    return h


def _render_quote(c: Dict[str, Any]) -> str:
    q = c.get('quote', '')
    a = c.get('quote_author', '')
    ah = f"<p style='text-align:right;margin-top:10px;color:#4F81BD;font-weight:bold'>— {a}</p>" if a else ""
    return f'''<div style='background:#e8f4f8;border-left:5px solid #4F81BD;padding:25px;margin:20px 0;border-radius:0 8px 8px 0'><p style='font-size:18px;margin:0;color:#1a1a1a;font-style:italic;line-height:1.6'>"{q}"</p>{ah}</div>'''


def _render_metrics(c: Dict[str, Any]) -> str:
    ms = c.get('key_metrics', []) or []
    if not ms:
        return "<p style='color:#666'>No metrics</p>"
    h = "<div style='display:flex;gap:20px;margin-top:20px;flex-wrap:wrap'>"
    for m in ms:
        h += f'''<div style='flex:1;min-width:150px;background:#4F81BD;color:white;padding:25px;border-radius:8px;text-align:center;box-shadow:0 2px 8px rgba(79,129,189,0.3)'><div style='font-size:32px;font-weight:bold'>{m.get('value','N/A')}</div><div style='font-size:14px;margin-top:5px;opacity:0.9'>{m.get('label','')}</div></div>'''
    h += "</div>"
    return h


def _render_image(c: Dict[str, Any]) -> str:
    img = c.get('image', '')
    if img and isinstance(img, str) and img.startswith('image'):
        return f"<img src='{img}' style='width:100%;max-width:600px;border-radius:8px;margin:20px 0;border:2px solid #ddd'/>"
    return "<div style='background:#f0f0f0;padding:60px;text-align:center;border-radius:8px;margin:20px 0;border:2px dashed #ccc;color:#666;font-size:16px'>🖼️ Image Placeholder<br/><small>Add your image here</small></div>"


def _render_timeline(c: Dict[str, Any]) -> str:
    items = c.get('timeline_items', []) or []
    if not items:
        return "<p style='color:#666'>No timeline</p>"
    h = "<div style='border-left:4px solid #4F81BD;padding-left:25px;margin:20px 0;background:#f8f9fa;padding:20px;border-radius:0 8px 8px 0'>"
    for it in items:
        h += f"<div style='margin:20px 0;padding:10px;background:white;border-radius:8px;box-shadow:0 1px 4px rgba(0,0,0,0.1)'><div style='font-weight:bold;color:#4F81BD;font-size:16px'>📅 {it.get('date','')}</div><div style='margin-top:8px;font-size:14px;color:#333'>{it.get('description','')}</div></div>"
    h += "</div>"
    return h


def _render_conclusion(c: Dict[str, Any]) -> str:
    h = ""
    if c.get('main_text'):
        h += f"<h3 style='color:#4F81BD;text-align:center;font-size:24px;margin:30px 0;font-weight:bold'>{c['main_text']}</h3>"
    for b in c.get('bullet_points', []):
        h += f"<p style='text-align:center;font-size:16px;margin:10px 0;color:#1a1a1a'>✓ {b}</p>"
    return h
