import streamlit as st
import json

from core.db import init_db, save_project
from core.auth import login, signup
from core.groq_models import get_active_models
from core.content_engine import generate_content
from core.ppt_generator import generate_ppt
from core.editor_engine import render_editor
from core.pdf_export import export_pdf

# -------------------
# INIT DB FIRST
# -------------------
init_db()

st.set_page_config(layout="wide")

# -------------------
# SESSION INIT
# -------------------
if "user" not in st.session_state:
    st.session_state.user = None

if "content" not in st.session_state:
    st.session_state.content = None

# -------------------
# LOGIN
# -------------------
if not st.session_state.user:

    st.title("🔐 Login / Signup")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    if col1.button("Login"):
        if not u or not p:
            st.warning("Enter username & password")
        else:
            success, result = login(u, p)
            if success:
                st.session_state.user = result
                st.success("Login successful")
                st.rerun()
            else:
                st.error(result)

    if col2.button("Signup"):
        if not u or not p:
            st.warning("Enter username & password")
        else:
            success, msg = signup(u, p)
            if success:
                st.success(msg)
            else:
                st.error(msg)

    st.stop()

# -------------------
# MAIN APP
# -------------------
st.title("🚀 AI PPT Architect")

st.success(f"Logged in as: {st.session_state.user[1]}")

template = st.file_uploader("Upload PPT Template", type=["pptx"])
slides = st.slider("Slides", 1, 100, 10)
model = st.selectbox("Model", get_active_models())

prompt = st.text_area("Enter Topic")

# -------------------
# GENERATE
# -------------------
if st.button("Generate Slides"):
    with st.spinner("Generating..."):
        st.session_state.content = generate_content(prompt, model, slides)

# -------------------
# EDIT + EXPORT
# -------------------
if st.session_state.content:

    edited = render_editor(st.session_state.content)
    st.session_state.content = json.dumps(edited)

    col1, col2, col3 = st.columns(3)

    if col1.button("Generate PPT"):
        file = generate_ppt(template, st.session_state.content)
        st.download_button("Download PPT", open(file, "rb"))

    if col2.button("Download PDF"):
        pdf = export_pdf(st.session_state.content)
        st.download_button("Download PDF", open(pdf, "rb"))

    if col3.button("Save"):
        save_project(st.session_state.user[0], st.session_state.content)
        st.success("Saved")
