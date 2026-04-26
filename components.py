import streamlit as st

def render_user_message(query):
    st.markdown(f'<div class="user-msg">질문: {query}</div>', unsafe_allow_html=True)

def render_ai_report(response_text):
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.markdown(response_text)
    st.markdown('</div>', unsafe_allow_html=True)
