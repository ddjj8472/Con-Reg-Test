import streamlit as st
import time
from engine import get_gemini_response
from database import get_ordinance_data

# app.py 맨 윗부분에 추가
st.write("시스템 상태: 최신 엔진(v1) 적용 시도 중")

# 페이지 설정
st.set_page_config(page_title="용인시 건축 조례 지원 플랫폼", layout="wide")

# --- 1. 기록 저장 및 선택 관리를 위한 세션 상태 초기화 ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "selected_index" not in st.session_state:
    st.session_state.selected_index = None # 현재 열람 중인 기록의 번호

# 디자인 서식
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-size: 16px; }
    .report-card { padding: 25px; border-radius: 8px; background-color: #ffffff; border: 1px solid #eeeeee; line-height: 1.6; margin-bottom: 20px; }
    .user-msg { background-color: #e1f5fe; padding: 15px; border-radius: 8px; border-left: 5px solid #0288d1; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 좌측 사이드바
with st.sidebar:
    st.title("플랫폼 제어")
    st.success("시스템 정상 작동")
    
    if st.button("➕ 새 분석 시작", use_container_width=True):
        st.session_state.selected_index = None
        st.rerun()
        
    st.divider()
    st.subheader("시스템 메뉴")
    st.button("화면 모드 전환")
    st.button("플랫폼 가동 현황")
    st.button("데이터 관리 화면")
    
    st.divider()
    st.subheader("📁 대화 이력 (클릭 시 열람)")
    
    # --- 2. 기록 목록 생성 및 클릭 이벤트 처리 ---
    if st.session_state.chat_history:
        for i, chat in enumerate(reversed
