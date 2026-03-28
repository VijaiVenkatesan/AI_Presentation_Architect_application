from groq import Groq
import streamlit as st
from core.search_engine import fetch_search_data

def generate_content(prompt, model, slide_count):

    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    search_context = fetch_search_data(prompt)

    final_prompt = f"""
STRICT JSON ONLY.

Generate {slide_count} enterprise slides for: {prompt}

Use real-time data:
{search_context}

Format:
{{
 "slides":[
  {{
   "title":"",
   "bullet_points":[],
   "diagram_type":"",
   "image_prompt":""
  }}
 ]
}}
"""

    res = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": final_prompt}],
    )

    return res.choices[0].message.content
