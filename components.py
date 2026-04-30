import streamlit as st
import re

def render_user_message(query):
    st.markdown(f'<div class="user-msg">질문: {query}</div>', unsafe_allow_html=True)

def render_ai_report(response_text):
    #6가지 항목 구성(존재할시)볼드체로 표시
    titles = ["결론", "적용 지역", "핵심 근거", "세부 해석", "원문 링크", "담당 기관"]

    # 6개 항목이 모두 있으면 '결론까지'와 '적용 지역 이후'를 2개 박스로 분리
    fixed_format = all(
        re.search(rf"(?m)^\s*{re.escape(title)}\s*[:：]?", response_text)
        for title in titles
    )

    match = re.search(r"(?m)^\s*적용 지역\s*[:：]?", response_text)

    if fixed_format and match:
        first_box = response_text[:match.start()].strip()
        second_box = response_text[match.start():].strip()

        for title in titles:
            first_box = re.sub(
                rf"(?m)^(\s*{re.escape(title)}\s*[:：]?)",
                r"<strong>\1</strong>",
                first_box
            )
            second_box = re.sub(
                rf"(?m)^(\s*{re.escape(title)}\s*[:：]?)",
                r"<strong>\1</strong>",
                second_box
            )

        first_box = first_box.replace("\n", "<br>")
        second_box = second_box.replace("\n", "<br>")

        st.markdown(f'<div class="report-card">{first_box}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="report-card">{second_box}</div>', unsafe_allow_html=True)
        return

    for title in titles:
        response_text = re.sub(
            rf"(?m)^(\s*{re.escape(title)}\s*[:：]?)",
            r"<strong>\1</strong>",
            response_text
        )

    formatted_text = response_text.replace("\n", "<br>")
    st.markdown(f'<div class="report-card">{formatted_text}</div>', unsafe_allow_html=True)
