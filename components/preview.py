"""
Enhanced Preview Component - Matches PPT output more closely
"""
import streamlit as st
from typing import Dict, List, Any
import base64

def render_slide_preview(slide_data: Dict[str, Any], slide_index: int):
    """Render a single slide preview that matches PPT output"""
    
    layout = slide_data.get('layout', 'content')
    title = slide_data.get('title', '')
    content = slide_data.get('content', {})
    
    # Create slide container with PowerPoint-like styling
    slide_html = f"""
    <div style="
        background: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 40px;
        margin: 20px 0;
        min-height: 400px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        font-family: 'Segoe UI', Arial, sans-serif;
    ">
    """
    
    # Add title
    if title:
        slide_html += f"""
        <h2 style="
            color: #4F81BD;
            font-size: 28px;
            margin-bottom: 20px;
            border-bottom: 2px solid #4F81BD;
            padding-bottom: 10px;
        ">{title}</h2>
        """
    
    # Render based on layout
    if layout == 'content':
        slide_html += _render_content_layout(content)
    elif layout == 'two_column':
        slide_html += _render_two_column_layout(content)
    elif layout == 'chart':
        slide_html += _render_chart_layout(content)
    elif layout == 'table':
        slide_html += _render_table_layout(content)
    elif layout == 'quote':
        slide_html += _render_quote_layout(content)
    elif layout == 'metrics':
        slide_html += _render_metrics_layout(content)
    elif layout == 'image':
        slide_html += _render_image_layout(content)
    elif layout == 'timeline':
        slide_html += _render_timeline_layout(content)
    elif layout == 'conclusion':
        slide_html += _render_conclusion_layout(content)
    else:
        slide_html += _render_content_layout(content)
    
    slide_html += "</div>"
    
    st.markdown(slide_html, unsafe_allow_html=True)


def display_all_slides_preview(slides_data: List[Dict[str, Any]]):
    """Display all slides in preview mode"""
    st.subheader("📊 Slide Preview")
    
    if not slides_data:
        st.info("No slides to preview")
        return
    
    for idx, slide_data in enumerate(slides_data, 1):
        with st.expander(f"📝 Slide {idx} ({slide_data.get('layout', 'content')})", expanded=(idx == 1)):
            render_slide_preview(slide_data, idx)


def _render_content_layout(content: Dict[str, Any]) -> str:
    """Render content layout"""
    html = ""
    
    if content.get('main_text'):
        html += f"<p style='font-size: 16px; margin-bottom: 15px;'>{content['main_text']}</p>"
    
    for bullet in content.get('bullet_points', []):
        html += f"<p style='font-size: 14px; margin: 8px 0; padding-left: 20px;'>• {bullet}</p>"
    
    return html


def _render_two_column_layout(content: Dict[str, Any]) -> str:
    """Render two-column layout"""
    left = content.get('left_column', [])
    right = content.get('right_column', [])
    
    if isinstance(left, str):
        left = [left]
    if isinstance(right, str):
        right = [right]
    
    left_html = "".join([f"<p style='margin: 8px 0;'>• {item}</p>" for item in left])
    right_html = "".join([f"<p style='margin: 8px 0;'>• {item}</p>" for item in right])
    
    return f"""
    <div style='display: flex; gap: 30px;'>
        <div style='flex: 1;'>{left_html}</div>
        <div style='flex: 1;'>{right_html}</div>
    </div>
    """


def _render_chart_layout(content: Dict[str, Any]) -> str:
    """Render chart layout"""
    chart_data = content.get('chart', {})
    
    html = f"<h3 style='color: #4F81BD;'>📊 {chart_data.get('title', 'Chart')}</h3>"
    
    if chart_data.get('description'):
        html += f"<p style='font-size: 14px; margin: 10px 0;'>{chart_data['description']}</p>"
    
    if chart_data.get('data'):
        html += "<table style='width: 100%; border-collapse: collapse; margin-top: 15px;'>"
        html += "<tr style='background: #4F81BD; color: white;'><th style='padding: 10px; border: 1px solid #ddd;'>Metric</th><th style='padding: 10px; border: 1px solid #ddd;'>Value</th></tr>"
        for key, value in chart_data['data'].items():
            html += f"<tr><td style='padding: 8px; border: 1px solid #ddd;'>{key}</td><td style='padding: 8px; border: 1px solid #ddd;'>{value}</td></tr>"
        html += "</table>"
    
    return html


def _render_table_layout(content: Dict[str, Any]) -> str:
    """Render table layout"""
    table_data = content.get('table', {})
    
    if not table_data.get('headers'):
        return "<p>No table data available</p>"
    
    html = "<table style='width: 100%; border-collapse: collapse; margin-top: 15px;'>"
    html += "<tr style='background: #4F81BD; color: white;'>"
    for header in table_data['headers']:
        html += f"<th style='padding: 12px; border: 1px solid #ddd;'>{header}</th>"
    html += "</tr>"
    
    for row in table_data.get('data', []):
        html += "<tr>"
        for cell in row:
            html += f"<td style='padding: 10px; border: 1px solid #ddd; text-align: center;'>{cell}</td>"
        html += "</tr>"
    
    html += "</table>"
    return html


def _render_quote_layout(content: Dict[str, Any]) -> str:
    """Render quote layout"""
    quote = content.get('quote', '')
    author = content.get('quote_author', '')
    
    author_html = f"<p style='text-align: right; margin-top: 10px; color: #666;'>— {author}</p>" if author else ""
    
    return f"""
    <div style='
        background: #f5f5f5;
        border-left: 4px solid #4F81BD;
        padding: 20px;
        margin: 20px 0;
        font-style: italic;
    '>
        <p style='font-size: 18px; margin: 0;'>"{quote}"</p>
        {author_html}
    </div>
    """


def _render_metrics_layout(content: Dict[str, Any]) -> str:
    """Render metrics layout"""
    metrics = content.get('key_metrics', [])
    
    if not metrics:
        return "<p>No metrics data available</p>"
    
    html = "<div style='display: flex; gap: 20px; margin-top: 20px; flex-wrap: wrap;'>"
    for metric in metrics:
        html += f"""
        <div style='
            flex: 1;
            min-width: 150px;
            background: #4F81BD;
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        '>
            <div style='font-size: 32px; font-weight: bold;'>{metric.get('value', 'N/A')}</div>
            <div style='font-size: 14px; margin-top: 5px;'>{metric.get('label', '')}</div>
        </div>
        """
    html += "</div>"
    return html


def _render_image_layout(content: Dict[str, Any]) -> str:
    """Render image layout"""
    image_data = content.get('image', '')
    
    if image_data:
        if isinstance(image_data, str) and image_data.startswith('data:image'):
            return f"<img src='{image_data}' style='width: 100%; max-width: 600px; border-radius: 8px; margin: 20px 0;' />"
        else:
            return "<div style='background: #f0f0f0; padding: 40px; text-align: center; border-radius: 8px; margin: 20px 0;'>🖼️ Image Placeholder</div>"
    
    return "<p>No image data available</p>"


def _render_timeline_layout(content: Dict[str, Any]) -> str:
    """Render timeline layout"""
    items = content.get('timeline_items', [])
    
    if not items:
        return "<p>No timeline data available</p>"
    
    html = "<div style='border-left: 3px solid #4F81BD; padding-left: 20px; margin: 20px 0;'>"
    for item in items:
        html += f"""
        <div style='margin: 20px 0;'>
            <div style='font-weight: bold; color: #4F81BD;'>📅 {item.get('date', '')}</div>
            <div style='margin-top: 5px; font-size: 14px;'>{item.get('description', '')}</div>
        </div>
        """
    html += "</div>"
    return html


def _render_conclusion_layout(content: Dict[str, Any]) -> str:
    """Render conclusion layout"""
    html = ""
    
    if content.get('main_text'):
        html += f"<h3 style='color: #4F81BD; text-align: center; font-size: 24px; margin: 30px 0;'>{content['main_text']}</h3>"
    
    for bullet in content.get('bullet_points', []):
        html += f"<p style='text-align: center; font-size: 16px; margin: 10px 0;'>✓ {bullet}</p>"
    
    return html
