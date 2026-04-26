import streamlit as st
import time
from datetime import datetime
from engine import get_gemini_response
from database import get_ordinance_data
from style import apply_custom_style
from components import render_user_message, render_ai_report

# 1. 페이지 설정 (최상단)
st.set_page_config(page_title="용인시 건축 조례 지원 플랫폼", layout="wide")

# 2. 상태 변수 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# 3. 스타일 적용
apply_custom_style(st.session_state.dark_mode)

# 4. 사이드바 구성
with st.sidebar:
    st.title("⚙️ 플랫폼 제어")
    st.session_state.dark_mode = st.toggle("🌙 다크 모드", value=st.session_state.dark_mode)
    
    st.divider()
    st.subheader("📁 대화 이력")
    
    # --- 화면 좌측에 기록을 버튼으로 띄워주는 핵심 로직 ---
    if st.session_state.chat_history:
        # 최신 기록이 위로 오도록 뒤집어서(reversed) 출력
        for i, chat in enumerate(reversed(st.session_state.chat_history)):
            actual_index = len(st.session_state.chat_history) - 1 - i
            time_str = chat.get('time', '00:00:00')[11:16]
            
            # 질문이 너무 길면 잘라서 요약 표시
            query_summary = chat['query']
            if len(query_summary) > 12:
                query_summary = query_summary[:12] + "..."
            
            # 버튼을 클릭하면 해당 인덱스를 selected_index에 저장하고 새로고침
            if st.button(f"🕒 {time_str} | {query_summary}", key=f"hist_{actual_index}", use_container_width=True):
                st.session_state.selected_index = actual_index
                st.rerun()
    else:
        st.caption("저장된 분석 기록이 없습니다.")
    # --------------------------------------------------------

    st.divider()
    if st.button("🗑️ 전체 기록 삭제"):
        st.session_state.chat_history = []
        st.session_state.selected_index = None
        
        # storage.py의 파일 삭제 기능 호출
        from storage import clear_history
        clear_history() 
        
        st.rerun()

# 5. 메인 화면
st.write("시스템 상태: 🟢 엔진 정상 가동 중")
st.title("🏢 건축 조례 및 법령 해석 지원 플랫폼")

tabs = st.tabs(["1️⃣ 프로젝트 개요", "2️⃣ 인공지능 분석", "3️⃣ 건축 시뮬레이션", "4️⃣ 민원 양식 생성"])

# --- 탭 1: 개요 ---
with tabs[0]:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📌 1. 프로젝트 목적")
        st.write("건축 실무 현장의 비효율을 개선하고 행정 리스크를 방지합니다.")
    with col2:
        st.subheader("📍 2. 프로젝트 범위")
        st.write("용인시 및 경기도 건축 조례, 상위 법령 125개 데이터 통합.")

# --- 탭 2: AI 분석 (대화형 UI로 전면 수정) ---
with tabs[1]:
    st.write("") 

    # [중요] 기존 대화 내용을 먼저 화면에 뿌려줍니다.
    for chat in st.session_state.chat_history:
        render_user_message(chat["query"])
        render_ai_report(chat["response"])

    # 사용자 입력창
    user_query = st.chat_input("분석이 필요한 건축 규제를 입력해 주세요")
    
    if user_query:
        # 1. 화면에 사용자 질문 즉시 표시
        render_user_message(user_query)
        
        # 2. 로딩 상태 표시 및 데이터 처리
        with st.status("분석 진행 중...", expanded=True) as status:
            st.write("🔍 데이터베이스 탐색 중...")
            db_context = get_ordinance_data(user_query)
            
            st.write("🤖 AI 엔진 보고서 작성 중...")
            response_text = get_gemini_response(user_query, db_context)
            
            status.update(label="✅ 분석 완료", state="complete")

        # 3. 화면에 AI 답변 즉시 표시
        render_ai_report(response_text)

        # 4. 세션 히스토리에 저장 (이후 새로고침 시에도 유지됨)
        st.session_state.chat_history.append({
            "query": user_query,
            "response": response_text,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # 새로고침하여 입력창 비우기 (히스토리는 저장되어 위에서 다시 그려짐)
        st.rerun()

# --- 탭 3, 4 ---
with tabs[2]: st.warning("🚧 건축선 시각화 기능 준비 중")
with tabs[3]: st.warning("🚧 행정 민원 지원 기능 준비 중")
