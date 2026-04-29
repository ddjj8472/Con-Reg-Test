import streamlit as st

def render_user_message(query):
    st.markdown(f'<div class="user-msg">질문: {query}</div>', unsafe_allow_html=True)

def render_ai_report(response_text):
    formatted_text = response_text.replace("\n", "<br>")
    st.markdown(f'<div class="report-card">{formatted_text}</div>', unsafe_allow_html=True)
