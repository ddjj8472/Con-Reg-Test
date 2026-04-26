import streamlit as st
import time
from engine import get_gemini_response
from database import get_ordinance_data

# 페이지 설정
st.set_page_config(page_title="용인시 건축 조례 지원 플랫폼", layout="wide")

# --- 1. 기록 저장(Session State) 초기화 ---
# 대화 이력을 저장할 리스트를 생성합니다.
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 디자인 서식
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-size: 16px; }
    .report-card { padding: 25px; border-radius: 8px; background-color: #ffffff; border: 1px solid #eeeeee; line-height: 1.6; margin-bottom: 20px; }
    .user-msg { background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 좌측 사이드바
with st.sidebar:
    st.title("플랫폼 제어")
    st.success("시스템 정상 작동")
    st.divider()
    st.subheader("시스템 메뉴")
    if st.button("대화 기록 초기화"):
        st.session_state.chat_history = []
        st.rerun()
    
    st.divider()
    st.subheader("실시간 대화 이력")
    # --- 2. 사이드바에 저장된 기록 표시 ---
    if st.session_state.chat_history:
        for i, chat in enumerate(reversed(st.session_state.chat_history)):
            # 질문의 앞부분만 잘라서 요약 형식으로 표시
            st.caption(f"{i+1}. {chat['query'][:15]}...")
    else:
        st.caption("이전 대화가 없습니다.")
    
    st.divider()
    st.button("사용자 접속 및 등록")

# 상단 제목
st.title("건축 조례 및 법령 해석 지원 플랫폼")

tab_list = ["1. 프로젝트 개요", "2. 인공지능 분석", "3. 건축 시뮬레이션", "4. 민원 양식 생성"]
tabs = st.tabs(tab_list)

# 1. 프로젝트 개요
with tabs[0]:
    st.header("프로젝트 개요")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("1. 프로젝트 목적")
        st.write("건축 실무 현장의 효율성 개선 및 행정 불이익 방지")
    with col2:
        st.subheader("2. 프로젝트 범위")
        st.write("경기도 용인시 조례 및 상위 법령 통합 분석")

# 2. 인공지능 분석 탭
with tabs[1]:
    st.header("인공지능 규제 분석")
    
    # --- 3. 과거 기록 먼저 출력 ---
    for chat in st.session_state.chat_history:
        with st.container():
            st.markdown(f'<div class="user-msg">질문: {chat["query"]}</div>', unsafe_allow_html=True)
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.write(chat["response"])
            st.markdown('</div>', unsafe_allow_html=True)

    # 새로운 질문 입력
    user_query = st.chat_input("분석이 필요한 건축 규제에 대해 입력해 주세요")
    
    if user_query:
        # 화면에 즉시 사용자 질문 표시
        st.markdown(f'<div class="user-msg">질문: {user_query}</div>', unsafe_allow_html=True)
        
        with st.status("단계별 규제 분석 진행 중...", expanded=True) as status:
            st.write("쟁점 파악 및 데이터 검색 중")
            time.sleep(0.5)
            
            # 데이터 및 AI 답변 생성
            db_info = get_ordinance_data(user_query)
            if db_info:
                full_response = f"""
                **1. 판단 결론:** {db_info['conclusion']}  
                **2. 적용 지역:** {db_info['region']}  
                **3. 핵심 근거 조문:** {db_info['law']}  
                **4. 해석 설명:** {db_info['detail']}  
                **5. 추가 확인 사항:** {db_info['check']}  
                **6. 후속 절차:** {db_info['next']}
                """
            else:
                full_response = get_gemini_response(user_query)
            
            status.update(label="분석 완료", state="complete", expanded=False)

        # 결과 출력
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.write(full_response)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- 4. 새로운 대화 내용을 기록에 추가 ---
        st.session_state.chat_history.append({
            "query": user_query,
            "response": full_response
        })
        
        # 사이드바 갱신을 위해 리런
        st.rerun()

# 3. 및 4. 탭
with tabs[2]:
    st.header("건축선 시각화")
    st.write("준비 중인 기능입니다.")
with tabs[3]:
    st.header("행정 민원 지원")
    st.write("준비 중인 기능입니다.")

st.divider()
st.caption("본 서비스는 행정기관의 최종 유권해석을 대체하지 않습니다.")
