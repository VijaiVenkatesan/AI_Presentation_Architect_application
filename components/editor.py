"""Slide Editor Component"""
import streamlit as st
from typing import Dict, List, Any
import copy

def render_slide_editor():
    if not st.session_state.get('slides'):
        st.info("No slides. Generate first.")
        return
    
    slides = st.session_state.slides
    col1, col2, col3 = st.columns([1,2,1])
    with col1:
        if st.button("◀ Prev", use_container_width=True) and st.session_state.current_slide_index > 0:
            st.session_state.current_slide_index -= 1
            st.rerun()
    with col2:
        st.write(f"**Slide {st.session_state.current_slide_index+1} of {len(slides)}**")
    with col3:
        if st.button("Next ▶", use_container_width=True) and st.session_state.current_slide_index < len(slides)-1:
            st.session_state.current_slide_index += 1
            st.rerun()
    
    st.divider()
    cs = slides[st.session_state.current_slide_index]
    col_a, col_b = st.columns([2,1])
    with col_a:
        new_title = st.text_input("Title", value=cs.get('title',''), key=f"t_{st.session_state.current_slide_index}")
        layouts = ['title','content','two_column','chart','table','quote','metrics','timeline','image','conclusion']
        new_layout = st.selectbox("Layout", layouts, index=layouts.index(cs.get('layout','content')) if cs.get('layout') in layouts else 1, key=f"l_{st.session_state.current_slide_index}")
    with col_b:
        st.metric("Layout", cs.get('layout','content'))
        st.metric("Slide #", cs.get('slide_number', st.session_state.current_slide_index+1))
    
    st.divider()
    st.subheader("📝 Content")
    content = cs.get('content', {})
    
    if new_layout == 'content':
        mt = st.text_area("Main Text", value=content.get('main_text',''), height=100)
        bp = st.text_area("Bullets (one per line)", value="\n".join(content.get('bullet_points',[])), height=150)
        if st.button("💾 Save", key="sv_c"):
            slides[st.session_state.current_slide_index].update({'title':new_title,'layout':new_layout,'content':{'main_text':mt,'bullet_points':[x.strip() for x in bp.split('\n') if x.strip()]}})
            st.success("✅ Saved")
    
    elif new_layout == 'two_column':
        lc = st.text_area("Left", value="\n".join(content.get('left_column',[])) if isinstance(content.get('left_column'),list) else content.get('left_column',''), height=200)
        rc = st.text_area("Right", value="\n".join(content.get('right_column',[])) if isinstance(content.get('right_column'),list) else content.get('right_column',''), height=200)
        if st.button("💾 Save", key="sv_2c"):
            slides[st.session_state.current_slide_index].update({'title':new_title,'layout':new_layout,'content':{'left_column':[x.strip() for x in lc.split('\n') if x.strip()],'right_column':[x.strip() for x in rc.split('\n') if x.strip()]}})
            st.success("✅ Saved")
    
    elif new_layout == 'chart':
        ct = st.text_input("Chart Title", value=content.get('chart',{}).get('title',''))
        cd = st.text_area("Description", value=content.get('chart',{}).get('description',''), height=100)
        cdt = st.text_area("Data (key: value)", value="\n".join([f"{k}: {v}" for k,v in content.get('chart',{}).get('data',{}).items()]), height=200)
        if st.button("💾 Save", key="sv_ch"):
            dd = {}
            for ln in cdt.split('\n'):
                if ':' in ln: k,v = ln.split(':',1); dd[k.strip()] = v.strip()
            slides[st.session_state.current_slide_index].update({'title':new_title,'layout':new_layout,'content':{'chart':{'title':ct,'description':cd,'data':dd}}})
            st.success("✅ Saved")
    
    elif new_layout == 'table':
        hdrs = st.text_input("Headers (comma)", value=",".join(content.get('table',{}).get('headers',[])))
        rows = st.text_area("Rows (comma-sep, one per line)", value="\n".join([",".join(r) for r in content.get('table',{}).get('data',[])]), height=200)
        if st.button("💾 Save", key="sv_tb"):
            slides[st.session_state.current_slide_index].update({'title':new_title,'layout':new_layout,'content':{'table':{'headers':[h.strip() for h in hdrs.split(',') if h.strip()],'data':[[c.strip() for c in r.split(',')] for r in rows.split('\n') if r.strip()]}}})
            st.success("✅ Saved")
    
    elif new_layout == 'quote':
        qt = st.text_area("Quote", value=content.get('quote',''), height=100)
        qa = st.text_input("Author", value=content.get('quote_author',''))
        if st.button("💾 Save", key="sv_qt"):
            slides[st.session_state.current_slide_index].update({'title':new_title,'layout':new_layout,'content':{'quote':qt,'quote_author':qa}})
            st.success("✅ Saved")
    
    elif new_layout == 'metrics':
        mi = st.text_area("Metrics (label: value)", value="\n".join([f"{m.get('label','')}: {m.get('value','')}" for m in content.get('key_metrics',[])]), height=200)
        if st.button("💾 Save", key="sv_mt"):
            ml = []
            for ln in mi.split('\n'):
                if ':' in ln: l,v = ln.split(':',1); ml.append({'label':l.strip(),'value':v.strip()})
            slides[st.session_state.current_slide_index].update({'title':new_title,'layout':new_layout,'content':{'key_metrics':ml}})
            st.success("✅ Saved")
    
    elif new_layout == 'image':
        idesc = st.text_area("Image Description", value=content.get('image','') if isinstance(content.get('image'),str) and not content.get('image').startswith('image') else '', height=100)
        st.info("📌 Images auto-generated by AI. Manual upload coming soon.")
        if st.button("💾 Save", key="sv_img"):
            slides[st.session_state.current_slide_index].update({'title':new_title,'layout':new_layout,'content':{'image':idesc}})
            st.success("✅ Saved")
    
    elif new_layout == 'timeline':
        ti = st.text_area("Timeline (date: desc)", value="\n".join([f"{t.get('date','')}: {t.get('description','')}" for t in content.get('timeline_items',[])]), height=200)
        if st.button("💾 Save", key="sv_tl"):
            tl = []
            for ln in ti.split('\n'):
                if ':' in ln: d,desc = ln.split(':',1); tl.append({'date':d.strip(),'description':desc.strip()})
            slides[st.session_state.current_slide_index].update({'title':new_title,'layout':new_layout,'content':{'timeline_items':tl}})
            st.success("✅ Saved")
    
    elif new_layout == 'conclusion':
        mt = st.text_area("Conclusion", value=content.get('main_text',''), height=100)
        bp = st.text_area("Key Points", value="\n".join(content.get('bullet_points',[])), height=150)
        if st.button("💾 Save", key="sv_cn"):
            slides[st.session_state.current_slide_index].update({'title':new_title,'layout':new_layout,'content':{'main_text':mt,'bullet_points':[x.strip() for x in bp.split('\n') if x.strip()]}})
            st.success("✅ Saved")
    
    st.divider()
    st.subheader("⚙️ Manage")
    col_x, col_y, col_z = st.columns(3)
    with col_x:
        if st.button("➕ Add Slide", use_container_width=True):
            slides.append({'slide_number':len(slides)+1,'layout':'content','title':'New Slide','content':{'main_text':'','bullet_points':[]}})
            st.session_state.slides = slides
            st.session_state.current_slide_index = len(slides)-1
            st.rerun()
    with col_y:
        if st.button("🗑️ Delete", use_container_width=True, disabled=len(slides)<=1):
            slides.pop(st.session_state.current_slide_index)
            for i,s in enumerate(slides): s['slide_number'] = i+1
            st.session_state.slides = slides
            if st.session_state.current_slide_index >= len(slides): st.session_state.current_slide_index = len(slides)-1
            st.rerun()
    with col_z:
        if st.button("📋 Duplicate", use_container_width=True):
            ns = copy.deepcopy(slides[st.session_state.current_slide_index])
            ns['slide_number'] = len(slides)+1
            ns['title'] = f"{ns['title']} (Copy)"
            slides.insert(st.session_state.current_slide_index+1, ns)
            for i,s in enumerate(slides): s['slide_number'] = i+1
            st.session_state.slides = slides
            st.session_state.current_slide_index += 1
            st.rerun()
