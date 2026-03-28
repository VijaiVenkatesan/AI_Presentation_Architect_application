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

    col1, col2 = st.columns(2)

    if col1.button("Login"):
        user = login(u, p)
        if user:
            st.session_state.user = user
            st.rerun()

    if col2.button("Signup"):
        if signup(u, p):
            st.success("Account created")

    st.stop()

# APP
st.title("🚀 Enterprise AI PPT Architect")

template = st.file_uploader("Upload PPT Template", type=["pptx"])
slides = st.slider("Slides", 1, 100, 10)
model = st.selectbox("Model", get_active_models())

prompt = st.text_area("Enter Topic")

if "content" not in st.session_state:
    st.session_state.content = None

if st.button("Generate Slides"):
    with st.spinner("Generating..."):
        st.session_state.content = generate_content(prompt, model, slides)

if st.session_state.content:

    st.subheader("Edit Slides")
    edited = render_editor(st.session_state.content)
    st.session_state.content = json.dumps(edited)

    if template and st.button("Generate PPT"):
        file = generate_ppt(template, st.session_state.content)
        st.download_button("Download PPT", open(file, "rb"))

    if st.button("Download PDF"):
        pdf = export_pdf(st.session_state.content)
        st.download_button("Download PDF", open(pdf, "rb"))

    if st.button("Save Project"):
        save_project(st.session_state.user[0], st.session_state.content)
        st.success("Saved")
