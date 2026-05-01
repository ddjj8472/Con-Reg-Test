import streamlit as st
import time
from datetime import datetime
import traceback
import inspect

from engine import get_gemini_response
from database import get_ordinance_data
from style import apply_custom_style
from components import render_user_message, render_ai_report
from storage import load_history, save_history 

# 1. 페이지 설정
st.set_page_config(page_title="용인시 건축 조례 지원 플랫폼", layout="wide")

# 2. 상태 변수 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_history()
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "selected_index" not in st.session_state:
    st.session_state.selected_index = None

# 3. 스타일 적용
apply_custom_style(st.session_state.dark_mode)

# 4. 사이드바 구성
with st.sidebar:
    st.title("⚙️ 플랫폼 제어")
    st.toggle("🌙 다크 모드", key="dark_mode") # key 사용으로 버튼 두번 클릭 버그 해결
    
    st.divider()
    if st.button("➕ 새 분석 시작", use_container_width=True, type="primary"):
        st.session_state.selected_index = None
        st.rerun()
        
    st.divider()
    st.subheader("📁 대화 이력 (클릭 시 열람)")
    
    if st.session_state.chat_history:
        for i, chat in enumerate(reversed(st.session_state.chat_history)):
            actual_index = len(st.session_state.chat_history) - 1 - i
            time_str = chat.get('time', '00:00:00')[11:16]
            
            query_summary = chat['query']
            if len(query_summary) > 12:
                query_summary = query_summary[:12] + "..."
            
            if st.button(f"🕒 {time_str} | {query_summary}", key=f"hist_{actual_index}", use_container_width=True):
                st.session_state.selected_index = actual_index
                st.rerun()
    else:
        st.caption("저장된 분석 기록이 없습니다.")

    st.divider()
    if st.button("🗑️ 전체 기록 삭제"):
        st.session_state.chat_history = []
        st.session_state.selected_index = None
        from storage import clear_history
        clear_history() 
        st.rerun()

# 5. 메인 화면
st.write("시스템 상태: 🟢 엔진 정상 가동 중")
st.title("🏢 건축 조례 및 법령 해석 지원 플랫폼")

with st.container():
    st.info("""
    **📌 프로젝트 목적:** 건축 실무 현장의 비효율을 개선하고 행정 리스크를 방지합니다.  
    **📍 프로젝트 범위:** 용인시 및 경기도 건축 조례, 상위 법령 125개 데이터 통합.
    """)

st.write("") 

# 🔥 [핵심] 검색창을 탭(tabs) 컨테이너 '바깥'으로 뺐습니다. 
# 이렇게 하면 Streamlit이 자동으로 화면 최하단에 검색창을 고정시켜 줍니다.
user_query = st.chat_input("분석이 필요한 건축 규제를 입력해 주세요")

tabs = st.tabs(["1️⃣ 인공지능 분석", "2️⃣ 건축 시뮬레이션", "3️⃣ 민원 양식 생성"])

# --- 탭 1: AI 분석 ---
with tabs[0]:
    st.write("") 

    if st.session_state.selected_index is not None:
        # 과거 열람 모드
        idx = st.session_state.selected_index
        selected_chat = st.session_state.chat_history[idx]
        
        st.success(f"📅 과거 분석 기록 열람 중 (조회 일시: {selected_chat.get('time', '')})")
        render_user_message(selected_chat["query"])
        render_ai_report(selected_chat["response"])
        
        if st.button("닫기 및 새 질문하기", use_container_width=True):
            st.session_state.selected_index = None
            st.rerun()

    else:
        # 새 질문 & 대화 모드
        for chat in st.session_state.chat_history:
            render_user_message(chat["query"])
            render_ai_report(chat["response"])

        if user_query:
            render_user_message(user_query)
            
            with st.status("분석 진행 중...", expanded=True) as status:
                try:
                    st.write("🔍 데이터베이스 탐색 중...")
                    db_context = get_ordinance_data(user_query)
                    
                    st.write("🤖 AI 엔진 보고서 작성 중...")
                    
                    sig = inspect.signature(get_gemini_response)
                    num_params = len(sig.parameters)
                    
                    if num_params == 1:
                        combined_prompt = f"질문: {user_query}\n\n참고법령: {db_context}" if db_context else user_query
                        response_text = get_gemini_response(combined_prompt)
                    else:
                        response_text = get_gemini_response(user_query, db_context)
                    
                    status.update(label="✅ 분석 완료", state="complete")

                    render_ai_report(response_text)
                    
                    st.session_state.chat_history.append({
                        "query": user_query,
                        "response": response_text,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    save_history(st.session_state.chat_history)
                    st.rerun()

                except Exception as e:
                    status.update(label="❌ 시스템 에러 발생", state="error")
                    st.error(f"코드 내부에서 에러가 발생했습니다: {str(e)}")
                    with st.expander("에러 상세 내용 보기 (추적 기록)"):
                        st.code(traceback.format_exc())

# --- 탭 2: 건축 시뮬레이션 ---
with tabs[1]:
    st.write("")
    st.warning("🚧 건축선 시각화 기능 준비 중")

# --- 탭 3: 민원 양식 생성 ---
with tabs[2]:
    st.write("")
    st.warning("🚧 행정 민원 지원 기능 준비 중")
