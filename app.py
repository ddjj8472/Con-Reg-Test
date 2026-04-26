import streamlit as st
import time
from datetime import datetime

# ==========================================
# 임시 가짜(Mock) 함수 (실제 연결 시 삭제)
# ==========================================
def get_ordinance_data(query):
    if "조례" in query:
        return {
            "conclusion": "조건부 허가 대상",
            "region": "경기도 용인시",
            "law": "용인시 건축 조례 제15조",
            "detail": f"입력하신 [{query}]와 관련하여, 용인시 조례에 따라 대지 안의 공지 기준을 충족해야 합니다.",
            "check": "해당 필지의 지구단위계획 포함 여부",
            "next": "관할 구청 건축과 사전 협의"
        }
    return None

def get_gemini_response(query):
    return f"AI 분석 엔진 응답: 입력하신 [{query}]에 대한 일반적인 건축 법령 가이드입니다. 구체적인 사항은 용인시 자치법규 시스템을 교차 검증해야 합니다."
# ==========================================

# 페이지 설정
st.set_page_config(page_title="용인시 건축 조례 지원 플랫폼", layout="wide")

# --- 1. 상태 변수 초기화 (다크 모드 추가) ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "selected_index" not in st.session_state:
    st.session_state.selected_index = None
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# --- 2. 좌측 사이드바 및 다크 모드 토글 ---
with st.sidebar:
    st.title("⚙️ 플랫폼 제어")
    
    # 다크 모드 스위치
    st.session_state.dark_mode = st.toggle("🌙 다크 모드 켜기", value=st.session_state.dark_mode)
    
    st.divider()
    
    if st.button("➕ 새 분석 시작", use_container_width=True, type="primary"):
        st.session_state.selected_index = None
        st.rerun()
        
    st.divider()
    st.subheader("📁 대화 이력 (클릭 시 열람)")
    
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

# --- 3. 다크/라이트 모드에 따른 동적 CSS 적용 ---
if st.session_state.dark_mode:
    # 다크 모드 색상 테마
    bg_main = "#0e1117"
    text_main = "#fafafa"
    card_bg = "#1e1e1e"
    card_border = "#333333"
    user_msg_bg = "#1e3a8a" # 짙은 파란색
    user_msg_text = "#ffffff"
    tab_color = "#aaaaaa"
else:
    # 라이트 모드 색상 테마 (기존)
    bg_main = "#f8f9fa"
    text_main = "#222222"
    card_bg = "#ffffff"
    card_border = "#eaeaea"
    user_msg_bg = "#e1f5fe" # 밝은 파란색
    user_msg_text = "#000000"
    tab_color = "#555555"

st.markdown(f"""
    <style>
    /* 전체 배경 덮어쓰기 (Streamlit 기본 컨테이너) */
    .stApp {{ background-color: {bg_main}; color: {text_main}; }}
    
    /* 폰트 및 텍스트 기본 설정 */
    html, body, [class*="css"] {{ font-size: 16px !important; line-height: 1.7 !important; color: {text_main}; }}
    
    /* 상단 탭 디자인 */
    .stTabs [data-baseweb="tab-list"] {{ gap: 15px; border-bottom: 2px solid {card_border}; }}
    .stTabs [data-baseweb="tab"] {{ height: 60px; font-size: 18px !important; font-weight: 600; color: {tab_color}; }}
    .stTabs [aria-selected="true"] {{ color: #1E88E5 !important; }}
    
    /* 결과 보고서 카드 디자인 */
    .report-card {{ 
        padding: 30px; border-radius: 12px; background-color: {card_bg}; 
        border: 1px solid {card_border}; color: {text_main};
        box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-top: 10px; margin-bottom: 20px; 
    }}
    
    /* 사용자 질문 박스 디자인 */
    .user-msg {{ 
        background-color: {user_msg_bg}; color: {user_msg_text};
        padding: 15px; border-radius: 8px; border-left: 5px solid #0288d1; margin-bottom: 10px; font-weight: bold;
    }}
    
    /* 버튼 텍스트 정렬 */
    .stButton>button {{ text-align: left !important; }}
    
    /* Streamlit 기본 텍스트 요소 색상 강제 적용 */
    p, h1, h2, h3, h4, h5, h6, li {{ color: {text_main} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 메인 화면 ---
st.write("시스템 상태: 🟢 최신 엔진(v1) 가동 중")
st.title("🏢 건축 조례 및 법령 해석 지원 플랫폼")
st.markdown("복잡한 건축 법령과 조례를 AI가 분석하여 직관적인 결과로 제공합니다.")
st.write("") 

tab_list = ["1️⃣ 프로젝트 개요", "2️⃣ 인공지능 분석", "3️⃣ 건축 시뮬레이션", "4️⃣ 민원 양식 생성"]
tabs = st.tabs(tab_list)

# 탭 1: 개요
with tabs[0]:
    st.write("") 
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📌 1. 프로젝트 목적")
        st.write("건축 실무 현장에서 반복되는 **법령 및 조례 해석의 비효율성을 개선**하고자 합니다.")
        st.write("조례를 잘못 해석하여 발생하는 **행정 불이익과 경제적 손실을 방지**하는 것을 핵심 목표로 합니다.")
    with col2:
        st.subheader("📍 2. 프로젝트 범위")
        st.write("**지역 범위 :** 경기도 용인시를 1차적 대상으로 합니다.")
        st.write("**데이터 범위 :** 용인시 조례와 경기도 조례, 그 상위 법령 13개와 차용법규 125개 규정을 통합합니다.")
    
    st.divider()
    st.subheader("⚙️ 3. 시스템 운영 체계")
    st.info("질문 분석부터 근거 추출 및 불확실성 검토까지 이어지는 **8단계 공정**을 거쳐 답변을 생성합니다.")

# 탭 2: AI 분석
with tabs[1]:
    st.write("") 

    if st.session_state.selected_index is not None:
        idx = st.session_state.selected_index
        selected_chat = st.session_state.chat_history[idx]
        
        st.success(f"📅 과거 분석 기록 열람 중 (조회 일시: {selected_chat['time']})")
        
        with st.chat_message("user"):
            st.markdown(f'<div class="user-msg">질문: {selected_chat["query"]}</div>', unsafe_allow_html=True)
            
        with st.chat_message("assistant"):
            st.markdown('<div class="report-card">', unsafe_allow_html=True)
            st.markdown(selected_chat["response"])
            st.markdown('</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("닫기 및 새 질문하기", use_container_width=True):
                st.session_state.selected_index = None
                st.rerun()

    else:
        user_query = st.chat_input("분석이 필요한 건축 규제에 대해 입력해 주세요 (예: 용인시 조례 알려줘)")
        
        if user_query:
            with st.chat_message("user"):
                st.markdown(f'<div class="user-msg">질문: {user_query}</div>', unsafe_allow_html=True)
            
            with st.chat_message("assistant"):
                with st.status("분석 진행 중...", expanded=True) as status:
                    st.write("🔍 쟁점 파악 및 데이터 검색 중...")
                    time.sleep(1) 
                    db_info = get_ordinance_data(user_query)
                    
                    if db_info:
                        response_text = f"""
                        ### 📑 검토 보고서
                        
                        **1. 판단 결론:** `{db_info['conclusion']}`  
                        **2. 적용 지역:** {db_info['region']}  
                        **3. 핵심 근거 조문:** **{db_info['law']}** **4. 해석 설명:** {db_info['detail']}  
                        
                        **5. 추가 확인 사항:** > ⚠️ {db_info['check']}  
                        
                        **6. 후속 절차:** {db_info['next']}
                        """
                    else:
                        response_text = get_gemini_response(user_query)
                    
                    status.update(label="✅ 분석 완료", state="complete")

                st.markdown('<div class="report-card">', unsafe_allow_html=True)
                st.markdown(response_text)
                st.markdown('</div>', unsafe_allow_html=True)

            new_record = {
                "query": user_query,
                "response": response_text,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            st.session_state.chat_history.append(new_record)
            st.rerun()

# 탭 3, 4
with tabs[2]:
    st.write("")
    st.warning("🚧 건축선 시각화 기능은 현재 준비 중입니다.")
with tabs[3]:
    st.write("")
    st.warning("🚧 행정 민원 지원 기능은 현재 준비 중입니다.")

st.divider()
st.caption("※ 본 서비스는 행정기관의 최종 유권해석을 대체하지 않습니다.")
