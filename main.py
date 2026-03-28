import streamlit as st
import json

from core.db import init_db, save_project
from core.auth import login, signup
from core.groq_models import get_active_models
from core.content_engine import generate_content
from core.ppt_generator import generate_ppt
from core.editor_engine import render_editor
from core.pdf_export import export_pdf

init_db()

# LOGIN
if "user" not in st.session_state:
    st.session_state.user = None

if not st.session_state.user:
    st.title("Login / Signup")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login(u, p)
        if user:
            st.session_state.user = user
            st.rerun()

    if st.button("Signup"):
        signup(u, p)

    st.stop()

# APP
st.title("🚀 AI PPT Architect")

template = st.file_uploader("Upload Template", type=["pptx"])
slides = st.slider("Slides", 1, 100, 10)

model = st.selectbox("Model", get_active_models())
prompt = st.text_area("Enter Topic")

if "content" not in st.session_state:
    st.session_state.content = None

if st.button("Generate"):
    st.session_state.content = generate_content(prompt, model, slides)

if st.session_state.content:
    edited = render_editor(st.session_state.content)
    st.session_state.content = json.dumps(edited)

    if st.button("Generate PPT"):
        file = generate_ppt(template, st.session_state.content)
        st.download_button("Download PPT", open(file, "rb"))

    if st.button("Download PDF"):
        pdf = export_pdf(st.session_state.content)
        st.download_button("Download PDF", open(pdf, "rb"))

    if st.button("Save"):
        save_project(st.session_state.user[0], st.session_state.content)
