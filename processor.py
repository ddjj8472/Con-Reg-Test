# processor.py
from datetime import datetime
import streamlit as st
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


# 민원 생성 함수
def generate_civil_document(civil_type, site_address, civil_content):
    """
    민원 양식 전용 생성 함수
    입력값을 바탕으로 민원서 기본 양식을 생성합니다.
    """

    return f"""
1. 민원 제목

{civil_type} 관련 민원

2. 대상 주소

{site_address}

3. 민원 유형

{civil_type}

4. 민원 요지 및 요청사항

민원인은 {site_address} 인근에서 발생한 건축 관련 문제로 인해 민원을 제기하고자 합니다.

구체적인 민원 내용은 다음과 같습니다.

{civil_content}

해당 사안에 대해 현장 확인 및 관련 법령, 조례 기준에 따른 검토를 요청드립니다. 또한 검토 결과에 따라 필요한 조치 가능 여부와 향후 처리 절차를 안내해 주시기 바랍니다.
"""
