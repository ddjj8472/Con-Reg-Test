import streamlit as st
import time
from engine import get_gemini_response
from database import get_ordinance_data

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
    .report-card { padding: 25px; border-radius: 8px; background-color: #ffffff; border: 1px solid #eeeeee; line-height: 1.6; margin-bottom: 20px; }
    .user-msg { background-color: #e1f5fe; padding: 15px; border-radius: 8px; border-left: 5px solid #0288d1; margin-bottom: 10px; }
    .history-btn { text-align: left !important; width: 100%; }
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
    st.subheader("📁 대화 이력 (클릭 시 열람)")
    
    # --- 2. 기록 목록 생성 및 클릭 이벤트 처리 ---
    if st.session_state.chat_history:
        for i, chat in enumerate(reversed(st.session_state.chat_history)):
            # 리스트 뒤집어서 최근 것이 위로 오게 함
            actual_index = len(st.session_state.chat_history) - 1 - i
            # 버튼을 클릭하면 해당 인덱스를 selected_index에 저장
            if st.button(f"📌 {chat['query'][:15]}...", key=f"hist_{actual_index}", use_container_width=True):
                st.session_state.selected_index = actual_index
                st.rerun()
    else:
        st.caption("저장된 기록이 없습니다.")
    
    st.divider()
    if st.button("전체 기록 삭제"):
        st.session_state.chat_history = []
        st.session_state.selected_index = None
        st.rerun()

# 상단 제목
st.title("건축 조례 및 법령 해석 지원 플랫폼")

tab_list = ["1. 프로젝트 개요", "2. 인공지능 분석", "3. 건축 시뮬레이션", "4. 민원 양식 생성"]
tabs = st.tabs(tab_list)

# 2. 인공지능 분석 탭 (기록 열람 및 질문 기능 집중)
with tabs[1]:
    st.header("인공지능 규제 분석")

    # --- 3. 특정 기록을 클릭해서 열람 중인 경우 ---
    if st.session_state.selected_index is not None:
        selected_chat = st.session_state.chat_history[st.session_state.selected_index]
        st.info(f"📅 과거 분석 기록 열람 중 (질문 일시: {selected_chat['time']})")
        
        st.markdown(f'<div class="user-msg">**질문 내용:** {selected_chat["query"]}</div>', unsafe_allow_html=True)
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.subheader("과거 검토 결과")
        st.write(selected_chat["response"])
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("닫기"):
            st.session_state.selected_index = None
            st.rerun()

    # --- 4. 새로운 질문 입력 (기존 결과 아래에 배치 또는 단독 배치) ---
    else:
        user_query = st.chat_input("분석이 필요한 건축 규제에 대해 입력해 주세요")
        
        if user_query:
            with st.status("용인시 건축 조례 분석 중...", expanded=True) as status:
                st.write("관련 법령 및 조례 검색 중")
                db_info = get_ordinance_data(user_query)
                
                if db_info:
                    response_text = f"""
                    **1. 판단 결론:** {db_info['conclusion']}  
                    **2. 적용 지역:** {db_info['region']}  
                    **3. 핵심 근거 조문:** {db_info['law']}  
                    **4. 해석 설명:** {db_info['detail']}  
                    **5. 추가 확인 사항:** {db_info['check']}  
                    **6. 후속 절차:** {db_info['next']}
                    """
                else:
                    response_text = get_gemini_response(user_query)
                
                status.update(label="분석 완료", state="complete")

            # 결과 출력
            st.markdown(f'<div class="user-msg">**신규 질문:** {user_query}</div>', unsafe_allow_html=True)
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.write(response_text)
            st.markdown('</div>', unsafe_allow_html=True)

            # --- 5. 기록 저장 (시간 정보 포함) ---
            new_record = {
                "query": user_query,
                "response": response_text,
                "time": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.chat_history.append(new_record)
            st.rerun()

# 1, 3, 4번 탭은 기존 내용 유지
with tabs[0]: st.write("프로젝트 개요 내용...")
with tabs[2]: st.write("준비 중...")
with tabs[3]: st.write("준비 중...")
