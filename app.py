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
# LOGIN / SIGNUP
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
                st.success("Login successful ✅")
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
st.title("🚀 Enterprise AI PPT Architect")

st.success(f"Logged in as: {st.session_state.user[1]}")

template = st.file_uploader("Upload PPT Template", type=["pptx"])
slides = st.slider("Slides", 1, 100, 10)
model = st.selectbox("Model", get_active_models())

prompt = st.text_area("Enter Topic")

# -------------------
# GENERATE
# -------------------
if st.button("Generate Slides"):
    if not prompt:
        st.warning("Please enter a topic")
    else:
        with st.spinner("Generating..."):
            try:
                st.session_state.content = generate_content(prompt, model, slides)
                st.success("Slides generated 🚀")
            except Exception as e:
                st.error(f"Error: {e}")

# -------------------
# EDIT + EXPORT
# -------------------
if st.session_state.content:

    st.subheader("✏️ Edit Slides")

    try:
        edited = render_editor(st.session_state.content)
        st.session_state.content = json.dumps(edited)
    except Exception as e:
        st.error(f"Editor error: {e}")

    st.divider()

    col1, col2, col3 = st.columns(3)

    # PPT DOWNLOAD
    if col1.button("📥 Generate PPT"):
        if not template:
            st.warning("Upload template first")
        else:
            try:
                file = generate_ppt(template, st.session_state.content)

                with open(file, "rb") as f:
                    st.download_button(
                        label="⬇️ Download PPT",
                        data=f.read(),
                        file_name="generated.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                    )

            except Exception as e:
                st.error(f"PPT error: {e}")

    # PDF DOWNLOAD
    if col2.button("📄 Download PDF"):
        try:
            pdf = export_pdf(st.session_state.content)

            with open(pdf, "rb") as f:
                st.download_button(
                    label="⬇️ Download PDF",
                    data=f.read(),
                    file_name="generated.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(f"PDF error: {e}")

    # SAVE PROJECT
    if col3.button("💾 Save Project"):
        try:
            save_project(st.session_state.user[0], st.session_state.content)
            st.success("Saved successfully ✅")
        except Exception as e:
            st.error(f"Save error: {e}")
