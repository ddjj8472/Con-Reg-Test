import streamlit as st
import time
from datetime import datetime
import traceback
import inspect
import streamlit.components.v1 as components # 카카오 지도를 위한 컴포넌트 추가

from engine import get_gemini_response
from database import get_ordinance_data
from style import apply_custom_style
from components import render_user_message, render_ai_report
from storage import load_history, save_history 

# 1. 페이지 설정 (화면을 넓게 쓰기 위해 layout="wide" 필수)
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
    st.toggle("🌙 다크 모드", key="dark_mode")
    
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

# --- 탭 구성 (스플릿 뷰를 1번 탭으로 통합) ---
tabs = st.tabs(["1️⃣ AI 규제 검토 & 지도 시뮬레이션", "2️⃣ 민원 양식 생성"])

# --- 탭 1: 전문가용 스플릿 뷰 (지도 + AI) ---
with tabs[0]:
    st.write("")
    
    # 화면을 5:5 비율로 분할 (gap="large"로 여유 공간 확보)
    col_map, col_chat = st.columns([1, 1], gap="large")
    
    # 📍 [좌측 화면] 카카오 지도 영역
    with col_map:
        st.subheader("🗺️ 대지 위치 및 건축선 시각화")
        
        KAKAO_JS_KEY = "본인의_카카오_자바스크립트_앱_키를_여기에_붙여넣으세요"
        
        map_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                #map {{
                    width: 100%;
                    height: 550px; /* 높이를 우측 채팅창과 맞춤 */
                    border-radius: 12px;
                    border: 1px solid #eaeaea;
                    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
                }}
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script type="text/javascript" src="//dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}"></script>
            <script>
                var mapContainer = document.getElementById('map'); 
                var mapOption = {{
                    center: new kakao.maps.LatLng(37.241086, 127.177553), // 용인시청 좌표
                    level: 4
                }};
                var map = new kakao.maps.Map(mapContainer, mapOption);
                var mapTypeControl = new kakao.maps.MapTypeControl();
                map.addControl(mapTypeControl, kakao.maps.ControlPosition.TOPRIGHT);
                var zoomControl = new kakao.maps.ZoomControl();
                map.addControl(zoomControl, kakao.maps.ControlPosition.RIGHT);
                
                // 전문가용 지적편집도 레이어 기본 추가
                map.addOverlayMapTypeId(kakao.maps.MapTypeId.USE_DISTRICT);
            </script>
        </body>
        </html>
        """
        
        if KAKAO_JS_KEY == "본인의_카카오_자바스크립트_앱_키를_여기에_붙여넣으세요":
            st.warning("🚧 카카오 JavaScript API 키를 코드에 입력해 주세요. (지도가 여기에 표시됩니다)")
        else:
            components.html(map_html, height=570)

    # 🤖 [우측 화면] AI 규제 검토 영역
    with col_chat:
        st.subheader("🤖 법규 규제 검토 및 질의응답")
        
        # 채팅 내역이 길어져도 지도를 넘어가지 않도록 스크롤 컨테이너 적용
        chat_box = st.container(height=480, border=False)
        
        with chat_box:
            # 1. 과거 기록 열람 모드
            if st.session_state.selected_index is not None:
                idx = st.session_state.selected_index
                selected_chat = st.session_state.chat_history[idx]
                
                st.success(f"📅 과거 분석 기록 열람 중 (조회 일시: {selected_chat.get('time', '')})")
                render_user_message(selected_chat["query"])
                render_ai_report(selected_chat["response"])
                
                if st.button("닫기 및 새 질문하기", use_container_width=True):
                    st.session_state.selected_index = None
                    st.rerun()
            
            # 2. 일반 대화 모드
            else:
                for chat in st.session_state.chat_history:
                    render_user_message(chat["query"])
                    render_ai_report(chat["response"])

        # 검색창 (col_chat 내부에 선언하여 우측 컨테이너 하단에 완벽하게 고정)
        user_query = st.chat_input("분석이 필요한 건축 규제를 입력해 주세요")

        if user_query:
            # 새 질문 입력 시 과거 열람 모드 강제 해제
            if st.session_state.selected_index is not None:
                st.session_state.selected_index = None

            with chat_box:
                render_user_message(user_query)
                
                with st.status("분석 진행 중...", expanded=True) as status:
                    try:
                        st.write("🔍 데이터베이스 탐색 중...")
                        db_context = get_ordinance_data(user_query)
                        
                        st.write("🤖 AI 엔진 보고서 작성 중...")
                        sig = inspect.signature(get_gemini_response)
                        if len(sig.parameters) == 1:
                            combined_prompt = f"질문: {user_query}\n\n참고법령: {db_context}" if db_context else user_query
                            response_text = get_gemini_response(combined_prompt)
                        else:
                            response_text = get_gemini_response(user_query, db_context)
                        
                        status.update(label="✅ 분석 완료", state="complete")

                    except Exception as e:
                        status.update(label="❌ 시스템 에러 발생", state="error")
                        st.error(f"코드 내부에서 에러가 발생했습니다: {str(e)}")
                        with st.expander("에러 상세 내용 보기"):
                            st.code(traceback.format_exc())
                        response_text = None

                if response_text:
                    render_ai_report(response_text)
                    st.session_state.chat_history.append({
                        "query": user_query,
                        "response": response_text,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    save_history(st.session_state.chat_history)
                    
            st.rerun()

# --- 탭 2: 민원 양식 생성 (기존 탭 3에서 변경) ---
with tabs[1]:
    st.write("")
    st.warning("🚧 행정 민원 지원 기능 준비 중")
