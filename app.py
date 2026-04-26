import streamlit as st
import time
from datetime import datetime

# 우리가 만든 모듈들 임포트
from engine import get_gemini_response
from database import get_ordinance_data
from style import apply_custom_style
@@ -14,129 +12,76 @@
# 2. 상태 변수 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "selected_index" not in st.session_state:
    st.session_state.selected_index = None
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# 3. 사이드바 구성
# 3. 스타일 적용
apply_custom_style(st.session_state.dark_mode)

# 4. 사이드바 구성
with st.sidebar:
    st.title("⚙️ 플랫폼 제어")
    
    # 다크 모드 토글
    st.session_state.dark_mode = st.toggle("🌙 다크 모드 켜기", value=st.session_state.dark_mode)
    
    st.divider()
    
    # 새 분석 시작 버튼
    if st.button("➕ 새 분석 시작", use_container_width=True, type="primary"):
        st.session_state.selected_index = None
        st.rerun()
        
    st.divider()
    st.subheader("📁 대화 이력 (클릭 시 열람)")
    
    # 이력 목록 출력 (최신순)
    if st.session_state.chat_history:
        for i, chat in enumerate(reversed(st.session_state.chat_history)):
            actual_index = len(st.session_state.chat_history) - 1 - i
            time_str = chat['time'][11:16]
            btn_text = f"🕒 {time_str} | {chat['query'][:12]}..."
            
            if st.button(btn_text, key=f"hist_{actual_index}", use_container_width=True):
                st.session_state.selected_index = actual_index
                st.rerun()
    else:
        st.info("저장된 분석 기록이 없습니다.")
    
    st.divider()
    if st.button("🗑️ 전체 기록 삭제"):
        st.session_state.chat_history = []
        st.session_state.selected_index = None
        st.rerun()

# 4. 스타일 적용 (style.py 호출)
apply_custom_style(st.session_state.dark_mode)

# 5. 메인 레이아웃
st.write("시스템 상태: 🟢 최신 엔진(v1) 가동 중")
# 5. 메인 화면
st.write("시스템 상태: 🟢 엔진 정상 가동 중")
st.title("🏢 건축 조례 및 법령 해석 지원 플랫폼")
st.markdown("복잡한 건축 법령과 조례를 AI가 분석하여 직관적인 결과로 제공합니다.")

# 탭 구성
tab_list = ["1️⃣ 프로젝트 개요", "2️⃣ 인공지능 분석", "3️⃣ 건축 시뮬레이션", "4️⃣ 민원 양식 생성"]
tabs = st.tabs(tab_list)
tabs = st.tabs(["1️⃣ 프로젝트 개요", "2️⃣ 인공지능 분석", "3️⃣ 건축 시뮬레이션", "4️⃣ 민원 양식 생성"])

# --- 탭 1: 개요 ---
with tabs[0]:
    st.write("") 
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📌 1. 프로젝트 목적")
        st.write("건축 실무 현장에서 반복되는 **법령 및 조례 해석의 비효율성을 개선**하고자 합니다.")
        st.write("조례를 잘못 해석하여 발생하는 **행정 불이익과 경제적 손실을 방지**하는 것을 핵심 목표로 합니다.")
        st.write("건축 실무 현장의 비효율을 개선하고 행정 리스크를 방지합니다.")
    with col2:
        st.subheader("📍 2. 프로젝트 범위")
        st.write("**지역 범위 :** 경기도 용인시를 1차적 대상으로 합니다.")
        st.write("**데이터 범위 :** 용인시 조례와 경기도 조례, 그 상위 법령 13개와 차용법규 125개 규정을 통합합니다.")
    
    st.divider()
    st.subheader("⚙️ 3. 시스템 운영 체계")
    st.info("질문 분석부터 근거 추출 및 불확실성 검토까지 이어지는 **8단계 공정**을 거쳐 답변을 생성합니다.")
        st.write("용인시 및 경기도 건축 조례, 상위 법령 125개 데이터 통합.")

# --- 탭 2: AI 분석 ---
# --- 탭 2: AI 분석 (대화형 UI로 전면 수정) ---
with tabs[1]:
    st.write("") 

    # 과거 기록 열람 모드
    if st.session_state.selected_index is not None:
        idx = st.session_state.selected_index
        selected_chat = st.session_state.chat_history[idx]
        
        st.success(f"📅 과거 분석 기록 열람 중 (조회 일시: {selected_chat['time']})")
        render_user_message(selected_chat["query"])
        render_ai_report(selected_chat["response"])
        
        if st.button("닫기 및 새 질문하기", use_container_width=True):
            st.session_state.selected_index = None
            st.rerun()
    # [중요] 기존 대화 내용을 먼저 화면에 뿌려줍니다.
    for chat in st.session_state.chat_history:
        render_user_message(chat["query"])
        render_ai_report(chat["response"])

    # 새 질문 모드
    else:
        user_query = st.chat_input("분석이 필요한 건축 규제를 입력해 주세요")
    # 사용자 입력창
    user_query = st.chat_input("분석이 필요한 건축 규제를 입력해 주세요")
    
    if user_query:
        # 1. 화면에 사용자 질문 즉시 표시
        render_user_message(user_query)

        if user_query:
            # 1. 사용자 질문 렌더링
            render_user_message(user_query)
        # 2. 로딩 상태 표시 및 데이터 처리
        with st.status("분석 진행 중...", expanded=True) as status:
            st.write("🔍 데이터베이스 탐색 중...")
            db_context = get_ordinance_data(user_query)
            
            st.write("🤖 AI 엔진 보고서 작성 중...")
            response_text = get_gemini_response(user_query, db_context)

            # 2. AI 분석 진행
            with st.status("분석 진행 중...", expanded=True) as status:
                st.write("🔍 조례 데이터베이스 및 상위 법령 검색 중...")
                # 실제 database.py의 검색 로직 실행
                db_context = get_ordinance_data(user_query)
                
                st.write("🤖 AI 엔진이 법리적 해석 및 보고서 작성 중...")
                # 실제 engine.py의 AI 호출 실행
                response_text = get_gemini_response(user_query, db_context)
                
                status.update(label="✅ 분석 완료", state="complete")
            status.update(label="✅ 분석 완료", state="complete")

            # 3. AI 결과 렌더링
            render_ai_report(response_text)
        # 3. 화면에 AI 답변 즉시 표시
        render_ai_report(response_text)

            # 4. 히스토리 저장 및 갱신
            st.session_state.chat_history.append({
                "query": user_query,
                "response": response_text,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            st.rerun()
        # 4. 세션 히스토리에 저장 (이후 새로고침 시에도 유지됨)
        st.session_state.chat_history.append({
            "query": user_query,
            "response": response_text,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # 새로고침하여 입력창 비우기 (히스토리는 저장되어 위에서 다시 그려짐)
        st.rerun()

# --- 탭 3, 4 ---
with tabs[2]:
    st.warning("🚧 건축선 시각화 기능은 현재 준비 중입니다.")
with tabs[3]:
    st.warning("🚧 행정 민원 지원 기능은 현재 준비 중입니다.")

st.divider()
st.caption("※ 본 서비스는 행정기관의 최종 유권해석을 대체하지 않습니다.")
with tabs[2]: st.warning("🚧 건축선 시각화 기능 준비 중")
with tabs[3]: st.warning("🚧 행정 민원 지원 기능 준비 중")
