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
    
    # 4. 세션 상태 업데이트 및 데이터 저장 (app.py 대신 여기서 처리)
    new_chat = {
        "query": user_query,
        "response": response_text,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    st.session_state.chat_history.append(new_chat)
    save_history(st.session_state.chat_history)
    
    return response_text
