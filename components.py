import streamlit as st
import re
import html
import json
import urllib.parse # [추가] 안전한 데이터 전송을 위해 필요

def render_user_message(query):
    """사용자 질문 출력"""
    st.markdown(
        f'<div class="user-msg">질문: {html.escape(query)}</div>',
        unsafe_allow_html=True
    )

def render_ai_report(response_text):
    """AI 답변 출력 + 소제목 정리 + 실제 작동하는 복사 버튼 (2026년 표준)"""

    titles = ["결론", "적용 지역", "핵심 근거", "세부 해석", "원문 링크", "담당 기관"]

    # 1. Markdown 제목 표시 제거
    response_text = re.sub(r"(?m)^\s*#{1,6}\s*", "", response_text)

    # 2. 소제목 정리 로직
    pattern = r"(?m)^\s*(" + "|".join(map(re.escape, titles)) + r")\s*[:：]?\s*(.*)$"
    def fix_heading(match):
        title = match.group(1)
        body = match.group(2).strip()
        return f"\n\n{title}\n{body}" if body else f"\n\n{title}"
    response_text = re.sub(pattern, fix_heading, response_text)
    response_text = re.sub(r"\n{3,}", "\n\n", response_text).strip()

    # 3. 화면 표시용 HTML 변환
    formatted_text = html.escape(response_text)

    # [조례 링크 괄호 잘림 방지용 패턴]
    # engine.py에서 보낸 [이름]|||주소||| 형식을 <a> 태그로 강제 변환
    formatted_text = re.sub(
        r"\[(.*?)\]\|\|\|(.*?)\|\|\|", 
        r'<a href="\2" target="_blank" style="color: #0b459c; text-decoration: underline; font-weight: bold;">\1</a>', 
        formatted_text
    )

    # 소제목 강조 처리
    for title in titles:
        formatted_text = re.sub(
            rf"(?m)^({re.escape(title)})$",
            r'<strong class="report-title">\1</strong>',
            formatted_text
        )
    formatted_text = formatted_text.replace("\n", "<br>")

    # 4. 복사용 텍스트 준비
    copy_text = json.dumps(response_text, ensure_ascii=False)

    # 5. [★ 핵심 수정: 복사 버튼 복구 및 경고 해결]
    # CSS의 '#' 기호가 URL을 깨뜨리지 않도록 안전하게 인코딩합니다.
    copy_button_html = f"""
    <div style="text-align:right; height:34px; overflow:hidden;">
        <button id="copyBtn" style="
            border:1px solid #ccc;
            background:white;
            border-radius:8px;
            padding:4px 9px;
            cursor:pointer;
            font-size:14px;
            font-family: sans-serif;
        ">📋 복사</button>
    </div>
    <script>
    const text = {copy_text};
    const btn = document.getElementById("copyBtn");
    btn.addEventListener("click", async () => {{
        try {{
            const ta = document.createElement("textarea");
            ta.value = text;
            ta.style.position = "fixed"; ta.style.left = "-9999px";
            document.body.appendChild(ta); ta.focus(); ta.select();
            document.execCommand("copy"); document.body.removeChild(ta);
            btn.innerText = "✅ 복사됨";
            setTimeout(() => btn.innerText = "📋 복사", 1200);
        }} catch (e) {{ btn.innerText = "복사 실패"; }}
    }});
    </script>
    """
    
    # [수정 포인트] urllib.parse.quote를 사용하여 HTML 코드를 안전한 주소 형식으로 변환합니다.
    encoded_html = urllib.parse.quote(copy_button_html)
    st.iframe(f"data:text/html;charset=utf-8,{encoded_html}", height=45)

    # 6. 최종 답변 카드 출력 (기존 디자인 유지)
    st.markdown(
        f'<div class="report-card">{formatted_text}</div>',
        unsafe_allow_html=True
    )
