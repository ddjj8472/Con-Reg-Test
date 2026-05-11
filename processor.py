# processor.py
from datetime import datetime
import streamlit as st
import requests
import json
import time

from engine import get_semantic_keywords, get_gemini_response
from database import get_ordinance_data
from storage import save_history


def handle_ai_analysis(user_query):
    """
    [UI-백엔드 브릿지 함수]
    app.py에서 이 함수만 호출하면 분석, DB탐색, 결과 저장까지 한 번에 끝냅니다.
    """
    # 1. 시맨틱 키워드 도출 (중요: 여기서 태그를 뽑아야 DB가 제13조를 찾습니다)
    semantic_tags = get_semantic_keywords(user_query)

    # 2. DB 탐색 (status와 context 확보)
    db_status, db_context = get_ordinance_data(user_query, semantic_tags)

    # 3. AI 응답 생성
    response_text = get_gemini_response(
        user_query=user_query,
        db_status=db_status,
        db_context=db_context,
        semantic_tags=semantic_tags
    )

    # 4. 대화방 방식으로 저장
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # chat_history가 없으면 빈 리스트 생성
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # selected_index가 없으면 None으로 생성
    if "selected_index" not in st.session_state:
        st.session_state.selected_index = None

    # 새 대화가 필요한 경우
    if st.session_state.selected_index is None or len(st.session_state.chat_history) == 0:
        new_chat = {
            "title": user_query[:20] + ("..." if len(user_query) > 20 else ""),
            "created_at": now,
            "updated_at": now,
            "messages": []
        }

        st.session_state.chat_history.append(new_chat)
        st.session_state.selected_index = len(st.session_state.chat_history) - 1

    # 현재 대화방 찾기
    current_chat = st.session_state.chat_history[st.session_state.selected_index]

    # 혹시 messages가 없으면 생성
    if "messages" not in current_chat:
        current_chat["messages"] = []

    # 현재 대화방 안에 질문/답변 추가
    current_chat["messages"].append({
        "query": user_query,
        "response": response_text,
        "time": now
    })

    current_chat["updated_at"] = now

    # 저장
    save_history(st.session_state.chat_history)

    return response_text


# 민원 생성용 LLM 호출 함수
def llm_invoke_function(system_prompt, user_prompt):
    """
    민원 양식 생성 전용 Gemini 호출 함수
    기존 processor.py의 system_prompt, user_prompt 구조를 그대로 사용합니다.
    """
    MODEL_NAME = "gemini-2.5-flash"
    api_key = st.secrets["GEMINI_API_KEY"]

    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {
        "Content-Type": "application/json"
    }

    prompt = f"""
{system_prompt}

[사용자 입력]
{user_prompt}
"""

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    for i in range(5):
        try:
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(payload),
                timeout=100
            )

            if response.status_code == 200:
                return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

            time.sleep(2)

        except Exception:
            time.sleep(2)

    return "민원서 생성 중 시스템 엔진 응답에 실패했습니다. 잠시 후 다시 시도해 주세요."


# 민원 생성 함수

def generate_civil_document(civil_type, site_address, civil_content):
    """
    민원 양식 전용 생성 함수
    """

    # LLM 호출 부분 (기존 설정 유지)

    system_prompt = f"""
    당신은 용인시청 건축부서에 제출할 민원서를 작성하는 전문 행정사입니다.
    사용자의 입력 정보를 바탕으로 '오직 민원서 양식'만 작성하여 바로 출력하세요.

    [작성 규칙]
    1. 반드시 아래 템플릿의 1번부터 4번까지만 작성하세요. 5번(법규 해석)이나 6번(검토 사항)은 절대 포함하지 마세요.
    2. 각 번호의 제목 뒤에는 반드시 한 줄의 줄바꿈을 넣어주세요. (예: 1. 민원 제목 [줄바꿈] 내용)
    3. 어조는 매우 정중하고 객관적인 행정 용어를 사용하세요.
    4. 내용은 핵심만 전달되도록 간소화하여 작성하세요.

    [민원서 템플릿]
    1. 민원 제목
    (제목 내용)

    2. 대상 주소
    {site_address}

    3. 민원 유형
    {civil_type}

    4. 민원 요지 및 요청사항
    (내용을 3~4문장 내외로 간소하게 작성)
    """

    user_prompt = f"다음 민원 내용을 바탕으로 양식을 생성해줘: {civil_content}"

    # LLM 호출 및 결과 반환
    return llm_invoke_function(system_prompt, user_prompt)
