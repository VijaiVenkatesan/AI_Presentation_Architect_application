import streamlit as st
import json
from utils.helpers import ensure_slide_structure

def render_editor(content_json):

    data = ensure_slide_structure(json.loads(content_json))
    updated = []

    for i, slide in enumerate(data["slides"]):

        st.markdown(f"### Slide {i+1}")

        title = st.text_input(f"title{i}", slide["title"])
        bullets = st.text_area(f"bullets{i}", "\n".join(slide["bullet_points"]))

        updated.append({
            "title": title,
            "bullet_points": bullets.split("\n"),
            "diagram_type": slide.get("diagram_type", ""),
            "image_prompt": slide.get("image_prompt", "")
        })

    return {"slides": updated}
