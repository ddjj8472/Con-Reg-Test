import streamlit as st
import re
import uuid

def render_user_message(query):
    st.markdown(f'<div class="user-msg">질문: {query}</div>', unsafe_allow_html=True)

def render_ai_report(response_text):
    #6가지 항목 구성(존재할시)볼드체로 표시
    titles = ["결론", "적용 지역", "핵심 근거", "세부 해석", "원문 링크", "담당 기관"]

    for title in titles:
        response_text = re.sub(
            rf"(?m)^(\s*{re.escape(title)}\s*[:：]?)",
            r'<strong class="report-title">\1</strong>',
            response_text
        )

    formatted_text = response_text.replace("\n", "<br>")
    box_id = f"copy_{uuid.uuid4().hex}"

    st.markdown(f"""
    <div class="report-wrapper">
        <button class="copy-btn"
            onclick="navigator.clipboard.writeText(document.getElementById('{box_id}').innerText)"
            title="답변 복사">📋 복사TEST</button>

        <div id="{box_id}" class="report-card">{formatted_text}</div>
    </div>
    """, unsafe_allow_html=True)
