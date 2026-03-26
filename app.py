import streamlit as st
from pptx import Presentation
from pptx.chart.data import ChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.shapes import PP_PLACEHOLDER
from pptx.util import Inches
import io
import json
from groq import Groq

# --- Page Configuration ---
st.set_page_config(page_title="True AI Presentation Architect", page_icon="🧠", layout="wide")

# --- 1. Dynamic Model Fetching (Re-integrated) ---
@st.cache_data(ttl=3600)
def get_available_groq_models(_client):
    """
    Fetches available, active LLM models directly from the Groq API to ensure
    the list is always up-to-date.
    """
    try:
        model_list = _client.models.list().data
        # Filter for active models suitable for chat/generation
        active_models = [m for m in model_list if m.active and "embedding" not in m.id]
        return sorted([model.id for model in active_models])
    except Exception as e:
        st.warning(f"Could not fetch live model list. Using a fallback. Error: {e}")
        # This fallback list is used ONLY if the API call to get models fails.
        return ["llama3-8b-8192", "mixtral-8x7b-32768", "gemma2-9b-it"]

# --- 2. AI-Driven Content Strategy ---
def generate_presentation_strategy(api_key, model, topic, num_slides):
    if not api_key: st.error("Groq API key not configured."); return None
    client = Groq(api_key=api_key)
    system_prompt = f"""
    You are a world-class business strategist. Create a diverse presentation strategy about '{topic}'.
    Your response MUST be a valid JSON object. The root object should have a "slides" key, containing an array of slide objects.
    Generate exactly {num_slides} unique slides.
    For each slide, provide a "type" which can be 'content', 'bar_chart', or 'table'.
    - 'content' slide: must have "title" (string) and "bullets" (array of strings).
    - 'bar_chart' slide: must have "title" (string) and "data" (an object with "categories" array and "series" array of objects with "name" and "values").
    - 'table' slide: must have "title" (string), "headers" (array of strings), and "rows" (array of arrays of strings).
    Ensure the data is realistic and properly structured for the slide type.
    """
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": f"Generate a {num_slides}-slide presentation strategy on: {topic}"}],
            model=model, temperature=0.8, response_format={"type": "json_object"},
        )
        response_data = json.loads(chat_completion.choices[0].message.content)
        # Find the actual list of slides within the returned JSON
        for key, value in response_data.items():
            if isinstance(value, list): return value
        st.error("AI did not return the expected slide array format."); return None
    except Exception as e:
        st.error(f"Groq API Error: Failed to generate presentation strategy. Details: {e}"); return None

# --- 3. Intelligent Template Analysis ---
@st.cache_data
def analyze_template(_template_file_bytes):
    prs = Presentation(io.BytesIO(_template_file_bytes))
    layout_map = {"content": [], "chart": [], "table": [], "title": None}
    for layout in prs.slide_layouts:
        placeholders = {p.placeholder_format.type for p in layout.placeholders}
        has_title = any(t in placeholders for t in [PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE])
        
        if has_title and not layout_map["title"]: layout_map["title"] = layout
        if has_title and PP_PLACEHOLDER.CHART in placeholders: layout_map["chart"].append(layout)
        elif has_title and PP_PLACEHOLDER.TABLE in placeholders: layout_map["table"].append(layout)
        elif has_title and PP_PLACEHOLDER.BODY in placeholders: layout_map["content"].append(layout)

    # Fallbacks: if specific layouts don't exist, use the general content layout
    if not layout_map["chart"] and layout_map["content"]: layout_map["chart"] = layout_map["content"]
    if not layout_map["table"] and layout_map["content"]: layout_map["table"] = layout_map["content"]
    
    return layout_map

# --- 4. Semantic Matching and Complex Population ---
def create_presentation_from_strategy(template_file, main_title, strategy):
    try:
        prs = Presentation(template_file)
        layout_map = analyze_template(template_file.getvalue())
    except Exception as e:
        st.error(f"❌ Error analyzing the template file: {e}"); return None

    # Clean existing slides
    for i in range(len(prs.slides) - 1, -1, -1):
        rId = prs.slides._sldIdLst[i].rId; prs.part.drop_rel(rId); del prs.slides._sldIdLst[i]
    
    # Add Title Slide
    title_layout = layout_map["title"] or (prs.slide_layouts[0] if len(prs.slide_layouts) > 0 else None)
    if not title_layout: st.error("Template has no suitable title layout."); return None
    slide = prs.slides.add_slide(title_layout)
    if slide.shapes.title: slide.shapes.title.text = main_title

    # Main Generation Loop
    for i, slide_data in enumerate(strategy):
        slide_type = slide_data.get("type", "content")
        layouts = layout_map.get(slide_type)
        if not layouts: st.warning(f"No layout found for type '{slide_type}'. Using general content layout."); layouts = layout_map["content"]
        if not layouts: st.error("No suitable content layouts found in template."); continue

        layout = layouts[i % len(layouts)]
        slide = prs.slides.add_slide(layout)
        if slide.shapes.title: slide.shapes.title.text = slide_data.get("title", "")

        # Populate based on slide type
        if slide_type == "content":
            body_shape = next((s for s in slide.placeholders if s.placeholder_format.type == PP_PLACEHOLDER.BODY), None)
            if body_shape:
                tf = body_shape.text_frame; tf.clear(); tf.word_wrap = True
                for bullet in slide_data.get("bullets", []): p = tf.add_paragraph(); p.text = str(bullet); p.level = 0
        
        elif slide_type == "bar_chart":
            chart_placeholder = next((s for s in slide.placeholders if s.placeholder_format.type == PP_PLACEHOLDER.CHART), None)
            if chart_placeholder:
                chart_data = ChartData(); chart_info = slide_data.get("data", {})
                chart_data.categories = chart_info.get("categories", [])
                for series in chart_info.get("series", []): chart_data.add_series(series.get("name", ""), [float(v) for v in series.get("values", [])])
                chart_placeholder.insert_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, chart_data)

        elif slide_type == "table":
            table_placeholder = next((s for s in slide.placeholders if s.placeholder_format.type == PP_PLACEHOLDER.TABLE), None)
            if table_placeholder:
                headers, rows_data = slide_data.get("headers", []), slide_data.get("rows", [])
                shape = table_placeholder.insert_table(rows=len(rows_data) + 1, cols=len(headers)); table = shape.table
                for c, h in enumerate(headers): table.cell(0, c).text = h
                for r, row in enumerate(rows_data):
                    for c, cell in enumerate(row): table.cell(r + 1, c).text = str(cell)

    bio = io.BytesIO(); prs.save(bio); bio.seek(0); return bio

# --- UI ---
st.title("🧠 True AI Presentation Architect")
st.markdown("Generates a complete presentation strategy with text, charts, and tables, then matches it to your enterprise template's specialized layouts.")

if 'strategy' not in st.session_state: st.session_state.strategy = []
if 'ppt_buffer' not in st.session_state: st.session_state.ppt_buffer = None

with st.sidebar:
    st.header("⚙️ Configuration")
    uploaded_template = st.file_uploader("1. Upload Your Enterprise Template (.pptx)", type="pptx")
    presentation_title = st.text_input("2. Main Presentation Title", "Q3 Sales Performance")
    topic = st.text_input("3. Presentation Topic", "A quarterly business review of our company's sales")
    num_slides = st.number_input("4. Number of Content Slides to Generate", 1, 50, 5)

    st.subheader("AI Engine")
    try:
        groq_api_key = st.secrets["GROQ_API_KEY"]; groq_client = Groq(api_key=groq_api_key)
        st.success("Groq API key loaded.", icon="✅")
    except: st.error("Groq API key not found."); groq_api_key = None; groq_client = None

    if groq_client:
        available_models = get_available_groq_models(groq_client)
        selected_model_id = st.selectbox("Select AI Model (Live from Groq)", options=available_models)
        
        if st.button("✨ Generate Presentation Strategy", type="primary", use_container_width=True):
            if not uploaded_template or not topic: st.warning("Please upload a template and enter a topic.")
            else:
                with st.spinner("🤖 AI is developing a multi-format presentation strategy..."):
                    strategy = generate_presentation_strategy(groq_api_key, selected_model_id, topic, num_slides)
                    if strategy:
                        st.session_state.strategy = strategy; st.session_state.ppt_buffer = None
                        st.toast("Strategy generated! Review and edit below."); st.rerun()

if st.session_state.ppt_buffer:
    st.success("✅ Your presentation is ready!")
    st.download_button("📥 Download Presentation", st.session_state.ppt_buffer, f"{presentation_title.replace(' ', '_')}.pptx", use_container_width=True)

if st.session_state.strategy:
    st.header("📝 Edit Strategy & Generate PPT")
    edited_strategy = st.session_state.strategy
    for i, slide in enumerate(edited_strategy):
        with st.expander(f"Slide {i+1}: **{slide.get('type', 'content').replace('_', ' ').title()}** - {slide.get('title', '...')}", expanded=True):
            edited_strategy[i]['title'] = st.text_input("Slide Title", value=slide.get("title", ""), key=f"title_{i}")
            if slide.get('type') == 'content':
                edited_strategy[i]['bullets'] = st.text_area("Bullet Points", "\n".join(slide.get("bullets", [])), key=f"bullets_{i}").split("\n")
            else: st.json(slide.get("data") or {"headers": slide.get("headers"), "rows": slide.get("rows")})
    
    if st.button("✅ Build My Presentation", use_container_width=True):
        with st.spinner("🏗️ Building presentation with complex objects..."):
            ppt_io = create_presentation_from_strategy(uploaded_template, presentation_title, edited_strategy)
            if ppt_io:
                st.session_state.ppt_buffer = ppt_io
                st.session_state.strategy = []
                st.rerun()
