"""AI Chat Interface - Fixed visibility and session state"""
import streamlit as st
from typing import Dict, List, Any

def render_chat_interface():
    llm = st.session_state.get('llm_handler')
    config = st.session_state.get('config')
    model = config.default_model if config else "llama-3.3-70b-versatile"
    
    if not llm or not llm.is_configured():
        st.error("❌ API not configured")
        return
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Check for pending message from quick actions
    if st.session_state.get('pending_message'):
        msg = st.session_state.pending_message
        st.session_state.pending_message = None
        st.session_state.chat_history.append({'role': 'user', 'content': msg})
        with st.spinner("🤔 Thinking..."):
            try:
                ctx = ""
                if st.session_state.get('slides'):
                    ctx = f"Presentation: {st.session_state.get('presentation_title','')}\nSlides: {len(st.session_state.slides)}\n"
                prompt = f"You are a presentation assistant.\n{ctx}\nUser: {msg}\nProvide helpful suggestions."
                resp = llm.generate_response(prompt=prompt, model=model, max_tokens=1000)
                st.session_state.chat_history.append({'role': 'assistant', 'content': resp or "Sorry, no response."})
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")
                st.session_state.chat_history.append({'role': 'assistant', 'content': f"Error: {e}"})
                st.rerun()
    
    # FIXED: High contrast styling
    st.markdown("""
    <style>
    .chat-msg { padding:1.5rem; border-radius:12px; margin-bottom:1.5rem; display:flex; gap:1rem; box-shadow:0 2px 8px rgba(0,0,0,0.1); }
    .chat-msg.user { background:linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; border-left:5px solid #667eea; }
    .chat-msg.assistant { background:#ffffff; color:#1a1a1a; border-left:5px solid #4CAF50; }
    .chat-avatar { width:45px; height:45px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:24px; background:#f0f0f0; flex-shrink:0; }
    .chat-content { flex:1; }
    .chat-content strong { display:block; margin-bottom:0.5rem; font-size:14px; opacity:0.8; }
    .chat-content p { margin:0; line-height:1.6; font-size:15px; }
    </style>""", unsafe_allow_html=True)
    
    st.subheader("💬 AI Chat Assistant")
    if not st.session_state.chat_history:
        st.info("👋 Ask me to help with your presentation!")
    
    for msg in st.session_state.chat_history:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        avatar = "👤" if role == 'user' else "🤖"
        css = "user" if role == 'user' else "assistant"
        st.markdown(f"""<div class="chat-msg {css}"><div class="chat-avatar">{avatar}</div><div class="chat-content"><strong>{'You' if role=='user' else 'AI Assistant'}</strong><p>{content}</p></div></div>""", unsafe_allow_html=True)
    
    st.divider()
    
    # Quick action buttons
    st.markdown("### ⚡ Quick Actions")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("📊 Add Chart Slide", use_container_width=True, key="btn_chart"):
            st.session_state.pending_message = "Add a chart slide showing trends"
            st.rerun()
    with col_b:
        if st.button("📋 Add Table Slide", use_container_width=True, key="btn_table"):
            st.session_state.pending_message = "Add a comparison table slide"
            st.rerun()
    with col_c:
        if st.button("🎯 Improve Content", use_container_width=True, key="btn_improve"):
            st.session_state.pending_message = "Improve the content of current slides"
            st.rerun()
    
    st.divider()
    
    # Text input
    st.subheader("✉️ Send a Message")
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input(
            "Your message",
            placeholder="Type your message here...",
            label_visibility="collapsed",
            key="chat_message_input"
        )
    with col2:
        send_btn = st.button("📤 Send", use_container_width=True, key="btn_send", type="primary")
    
    if send_btn and user_input:
        st.session_state.chat_history.append({'role': 'user', 'content': user_input})
        with st.spinner("🤔 AI is thinking..."):
            try:
                ctx = ""
                if st.session_state.get('slides'):
                    ctx = f"Presentation: {st.session_state.get('presentation_title','')}\nSlides: {len(st.session_state.slides)}\n"
                prompt = f"You are a presentation assistant.\n{ctx}\nUser: {user_input}\nProvide helpful, actionable suggestions."
                resp = llm.generate_response(prompt=prompt, model=model, max_tokens=1000)
                st.session_state.chat_history.append({'role': 'assistant', 'content': resp or "Sorry, no response."})
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")
                st.session_state.chat_history.append({'role': 'assistant', 'content': f"Error: {e}"})
                st.rerun()
    
    if st.button("🗑️ Clear Chat History", key="btn_clear"):
        st.session_state.chat_history = []
        st.rerun()
    
    with st.expander("⚙️ Chat Settings"):
        st.selectbox("Model", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"], index=0, key="chat_model_sel")
        st.slider("Temperature", 0.0, 1.0, 0.7, 0.1, key="chat_temp")
        st.slider("Max Tokens", 100, 4000, 1000, 100, key="chat_tokens")
