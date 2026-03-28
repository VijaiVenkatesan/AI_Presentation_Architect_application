import streamlit as st
from groq import Groq

@st.cache_data(ttl=3600)
def get_active_models():
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        models = client.models.list()

        valid = []
        for m in models.data:
            mid = m.id.lower()

            if any(k in mid for k in ["llama", "mixtral", "gemma"]) and not any(
                k in mid for k in ["vision", "audio", "whisper"]
            ):
                valid.append(m.id)

        return sorted(valid) or ["llama3-70b-8192"]

    except:
        return ["llama3-70b-8192"]
