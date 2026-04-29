import streamlit as st
import re
import html

def render_user_message(query):
    st.markdown(f'<div class="user-msg">질문: {query}</div>', unsafe_allow_html=True)

def render_ai_report(response_text):
    # 굵게 표시할 답변 제목 목록
    titles = ["결론", "적용 지역", "핵심 근거", "세부 해석", "원문 링크", "담당 기관"]

    # 이 제목부터는 두 번째 박스로 분리
    next_titles = ["적용 지역", "핵심 근거", "세부 해석", "원문 링크", "담당 기관"]

    def format_text(text):
        # HTML 태그 오인식 방지
        text = html.escape(text)

        # 줄 맨 앞에 있는 제목만 볼드 처리
        for title in titles:
            text = re.sub(
                rf"(?m)^(\s*{title}\s*[:：]?)",
                r"<strong>\1</strong>",
                text
            )

        # 줄바꿈 유지
        return text.replace("\n", "<br>")

    # 세부 항목이 시작되는 위치 찾기
    pattern = r"(?m)^\s*(" + "|".join(next_titles) + r")\s*[:：]?"
    match = re.search(pattern, response_text)

    if match:
        # 첫 번째 박스: 안내문 + 결론
        first_box = response_text[:match.start()].strip()

        # 두 번째 박스: 적용 지역 이후 내용
        second_box = response_text[match.start():].strip()

        st.markdown(
            f"""
            <div class="report-card">
                {format_text(first_box)}
            </div>

            <div class="report-card">
                {format_text(second_box)}
            </div>
            """,
            unsafe_allow_html=True
        )

    else:
        # 분리 기준이 없으면 기존처럼 하나의 박스로 출력
        st.markdown(
            f'<div class="report-card">{format_text(response_text)}</div>',
            unsafe_allow_html=True
        )
