import streamlit as st
import re
import html
import json
import textwrap

def render_user_message(query):
    st.markdown(
        f'<div class="user-msg">질문: {html.escape(query)}</div>',
        unsafe_allow_html=True
    )

def render_ai_report(response_text):
    titles = ["결론", "적용 지역", "핵심 근거", "세부 해석", "원문 링크", "담당 기관"]

    safe_text = html.escape(response_text)

    for title in titles:
        safe_text = re.sub(
            rf"(?m)^\s*(?:#+\s*)?{re.escape(title)}\s*[:：]?(?=\s|$)",
            f'<strong class="report-title">{title}</strong>',
            safe_text
        )

    formatted_text = safe_text.replace("\n", "<br>")
    copy_text = json.dumps(response_text, ensure_ascii=False)

    html_block = f"""
    <div class="report-wrapper">
        <button class="copy-btn"
            onclick='navigator.clipboard.writeText({copy_text})'
            title="답변 복사">📋 복사TEST</button>

        <div class="report-card">{formatted_text}</div>
    </div>
    """

    st.markdown(textwrap.dedent(html_block).strip(), unsafe_allow_html=True)
