import streamlit as st
import re

def render_user_message(query):
    st.markdown(f'<div class="user-msg">질문: {query}</div>', unsafe_allow_html=True)

def render_ai_report(response_text):
    #6가지 항목 구성(존재할시)볼드체로
    titles = ["결론", "적용 지역", "핵심 근거", "세부 해석", "원문 링크", "담당 기관"]

    for title in titles:
        response_text = re.sub(
            rf"(?m)^(\s*{re.escape(title)}\s*[:：]?)",
            r"<strong>\1</strong>",
            response_text
        )

    formatted_text = response_text.replace("\n", "<br>")
    st.markdown(f'<div class="report-card">{formatted_text}</div>', unsafe_allow_html=True)
