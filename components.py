import streamlit as st
import re
import html
import json


def render_user_message(query):
    """사용자 질문 출력"""
    st.markdown(
        f'<div class="user-msg">질문: {html.escape(query)}</div>',
        unsafe_allow_html=True
    )


def render_ai_report(response_text):
    """AI 답변 출력 + 소제목 정리 + 복사 버튼"""

    titles = ["결론", "적용 지역", "핵심 근거", "세부 해석", "원문 링크", "담당 기관"]

    # 1. AI가 붙이는 Markdown 제목 표시(### 결론 등) 제거
    response_text = re.sub(r"(?m)^\s*#{1,6}\s*", "", response_text)

    # 2. 소제목 형식 정리
    # 예: "핵심 근거 내용" → "핵심 근거\n내용"
    pattern = r"(?m)^\s*(" + "|".join(map(re.escape, titles)) + r")\s*[:：]?\s*(.*)$"

    def fix_heading(match):
        title = match.group(1)
        body = match.group(2).strip()

        if body:
            return f"\n\n{title}\n{body}"
        return f"\n\n{title}"

    response_text = re.sub(pattern, fix_heading, response_text)

    # 3. 너무 많은 빈 줄은 1칸 정도로 정리
    response_text = re.sub(r"\n{3,}", "\n\n", response_text).strip()

    # 4. 화면 표시용 HTML 처리
    formatted_text = html.escape(response_text)

    for title in titles:
        formatted_text = re.sub(
            rf"(?m)^({re.escape(title)})$",
            r'<strong class="report-title">\1</strong>',
            formatted_text
        )

    formatted_text = formatted_text.replace("\n", "<br>")

    # 5. 복사용 텍스트는 HTML이 아닌 정리된 원문 사용
    copy_text = json.dumps(response_text, ensure_ascii=False)

    html_block = (
        f'<div class="report-wrapper">'
        f'<button class="copy-btn" '
        f'onclick=\'navigator.clipboard.writeText({copy_text})\' '
        f'title="답변 복사">📋</button>'
        f'<div class="report-card">{formatted_text}</div>'
        f'</div>'
    )

    st.markdown(html_block, unsafe_allow_html=True)
