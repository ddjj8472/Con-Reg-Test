import streamlit as st
import time
from datetime import datetime
import traceback
import streamlit.components.v1 as components 

# [구조 분리] 백엔드 통합 프로세서로 교체
# 기존 process_architectural_query 대신 저장 기능까지 포함된 handle_ai_analysis를 사용합니다.
from processor import handle_ai_analysis 
from style import apply_custom_style
from components import render_user_message, render_ai_report
from storage import load_history, save_history 

# 1. 페이지 설정 (최상단)
st.set_page_config(page_title="용인시 건축 조례 지원 플랫폼", layout="wide")

# 2. 상태 변수 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_history()
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "selected_index" not in st.session_state:
    st.session_state.selected_index = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "main"

# [새로 추가된 부분] Q&A 게시판 데이터 저장용 리스트
if "qna_list" not in st.session_state:
    st.session_state.qna_list = []

# 3. 스타일 적용
apply_custom_style(st.session_state.dark_mode)

# 4. 사이드바 구성
with st.sidebar:
    st.title("⚙️ 플랫폼 제어")
    
    # [추가] 페이지 이동 네비게이션
    st.subheader("📌 메뉴")
    if st.button("🏠 메인 화면 (AI/민원)", use_container_width=True):
        st.session_state.current_page = "main"
        st.rerun()
    if st.button("💡 Q&A 게시판", use_container_width=True):
        st.session_state.current_page = "qna"
        st.rerun()
    if st.button("🗺️ 사이트맵", use_container_width=True):
        st.session_state.current_page = "sitemap"
        st.rerun()

    st.divider()
    st.toggle("🌙 다크 모드", key="dark_mode")
    
    st.divider()
    if st.button("➕ 새 분석 시작", use_container_width=True, type="primary"):
        st.session_state.selected_index = None
        st.session_state.current_page = "main" # 새 분석 시 메인으로 이동
        st.rerun()
        
    # (이하 기존 사이드바 코드: 대화 이력 열람, 전체 기록 삭제 등 유지)
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

# 5. 메인 화면 출력 (조건부 렌더링)
if st.session_state.current_page == "main":
    st.write("시스템 상태: 🟢 엔진 정상 가동 중")
    st.title("🏢 건축 조례 및 법령 해석 지원 플랫폼")

    with st.container():
        st.info("""
        **📌 프로젝트 목적:** 건축 실무 현장의 비효율을 개선하고 행정 리스크를 방지합니다.  
        **📍 프로젝트 범위:** 용인시 및 경기도 건축 조례, 상위 법령 125개 데이터 통합.
        """)
    st.write("") 

    user_query = st.chat_input("분석이 필요한 건축 규제를 입력해 주세요")
    tabs = st.tabs(["1️⃣ AI 규제 검토 & 지도 시뮬레이션", "2️⃣ 민원 양식 생성"])
    
    # (여기에 기존 탭 1, 탭 2의 상세 코드를 그대로 유지합니다)

    # --- 탭 1: 전문가용 스플릿 뷰 ---
    with tabs[0]:
        st.write("")
        
        col_chat, col_map = st.columns([1, 1], gap="large")
        
        # 🤖 [좌측 화면] AI 질의응답
        with col_chat:
            st.subheader("🤖 법규 규제 검토 및 질의응답")
            
            chat_box = st.container(height=520, border=False)
            
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
    
                    # 질문 처리 로직
                    if user_query:
                        render_user_message(user_query)
                        
                        with st.status("🔍 심층 분석 진행 중...", expanded=True) as status:
                            try:
                                st.write("🛰️ 법률 시맨틱 레이어 및 통합 엔진 가동 중...")
                                
                                # [핵심 변경] 
                                # 1. 기존의 process_architectural_query를 handle_ai_analysis로 교체했습니다.
                                # 2. 이 함수는 결과 생성뿐만 아니라 '기록 저장'까지 백엔드에서 수행합니다.
                                response_text = handle_ai_analysis(user_query)
                                
                                status.update(label="✅ 분석 완료", state="complete")
                                render_ai_report(response_text)
                                
                                # [핵심 제거] 
                                # 아래의 수동 저장 코드는 로직 안전을 위해 processor.py 내부로 이동되었습니다.
                                # - st.session_state.chat_history.append(...) -> 제거
                                # - save_history(...) -> 제거
                                
                            except Exception as e:
                                status.update(label="❌ 시스템 에러 발생", state="error")
                                st.error(f"시스템 처리 중 오류가 발생했습니다: {str(e)}")
                                with st.expander("에러 상세 내용 보기"):
                                    st.code(traceback.format_exc())
                                    
                        st.rerun()
    
        # 📍 [우측 화면] 카카오 지도 시각화 (팀원 코드 유지)
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
                        height: 570px; 
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
                        center: new kakao.maps.LatLng(37.241086, 127.177553), // 용인시청
                        level: 4
                    }};
                    var map = new kakao.maps.Map(mapContainer, mapOption);
                    var mapTypeControl = new kakao.maps.MapTypeControl();
                    map.addControl(mapTypeControl, kakao.maps.ControlPosition.TOPRIGHT);
                    var zoomControl = new kakao.maps.ZoomControl();
                    map.addControl(zoomControl, kakao.maps.ControlPosition.RIGHT);
                    map.addOverlayMapTypeId(kakao.maps.MapTypeId.USE_DISTRICT);
                </script>
            </body>
            </html>
            """
            
            if KAKAO_JS_KEY == "본인의_카카오_자바스크립트_앱_키를_여기에_붙여넣으세요":
                st.warning("🚧 카카오 JavaScript API 키를 코드에 입력해 주세요.")
            else:
                components.html(map_html, height=590)
    
    # --- 탭 2: 민원 양식 생성 ---
    with tabs[1]:
        st.write("")
        st.warning("🚧 행정 민원 지원 기능 준비 중")

# --- Q&A 게시판 화면 ---
elif st.session_state.current_page == "qna":
    st.title("💡 자주 묻는 질문 (FAQ) 및 Q&A")
    st.write("플랫폼 사용법 및 건축 법령 해석과 관련된 질문을 확인하고 남길 수 있습니다.")
    st.divider()
    
    # 1. 예시 질문 (ex 표시 추가)
    st.subheader("📌 자주 묻는 질문 (기본 예시)")
    with st.expander("ex) 이 플랫폼은 어떤 데이터를 바탕으로 답변하나요?"):
        st.write("A. 용인시/경기도 건축 조례 및 125개 상위 법령 데이터를 통합하여 답변합니다.")
    with st.expander("ex) 과거 분석 기록은 어떻게 확인하나요?"):
        st.write("A. 좌측 사이드바의 '대화 이력'에서 클릭하여 열람할 수 있습니다.")

    st.divider()

    # 2 & 3. 사용자 질문 목록 및 상태 표시 ('대기중' / '답변완료')
    st.subheader("📋 사용자 질문 목록")
    if len(st.session_state.qna_list) == 0:
        st.caption("아직 등록된 질문이 없습니다. 첫 번째 질문을 남겨보세요!")
    else:
        for i, q in enumerate(st.session_state.qna_list):
            # 상태에 따라 아이콘과 텍스트 변경
            status_badge = "🔴 대기중" if q['status'] == "대기중" else "🟢 답변완료"
            
            with st.expander(f"[{status_badge}] {q['title']}"):
                st.write(f"**Q. {q['content']}**")
                
                # 답변이 완료된 경우에만 답변 내용 표시
                if q['status'] == "답변완료":
                    st.info(f"**A. {q['answer']}**")

    st.divider()

    # 질문 등록 폼 (clear_on_submit=True로 설정하여 제출 후 폼 비우기)
    st.subheader("📝 새로운 질문 남기기")
    with st.form("qna_form", clear_on_submit=True):
        q_title = st.text_input("질문 제목")
        q_content = st.text_area("질문 내용 (구체적으로 작성해주세요)")
        if st.form_submit_button("질문 등록하기"):
            if q_title and q_content:
                # 새로운 질문 데이터를 딕셔너리 형태로 리스트에 추가
                new_question = {
                    "title": q_title,
                    "content": q_content,
                    "status": "대기중",  # 초기 상태는 무조건 대기중
                    "answer": ""
                }
                st.session_state.qna_list.append(new_question)
                st.success("질문이 성공적으로 등록되었습니다! 관리자 확인 후 답변이 달립니다.")
                st.rerun()  # 화면을 새로고침하여 목록에 즉시 반영
            else:
                st.error("제목과 내용을 모두 입력해 주세요.")

    st.divider()

    # 3. 관리자용 답변 작성 기능
    st.subheader("🛠️ 관리자 메뉴 (답변 달기)")
    admin_toggle = st.toggle("관리자 모드 켜기")
    
    if admin_toggle:
        admin_pw = st.text_input("관리자 비밀번호 입력", type="password")
        # 실제 서비스에서는 보안을 위해 강력한 비밀번호를 사용하세요. (현재는 2026)
        if admin_pw == "2026":
            st.success("관리자 인증 완료! 대기중인 질문에 답변을 달아주세요.")
            
            # 대기중인 질문만 필터링하여 답변 폼 생성
            pending_questions = [q for q in st.session_state.qna_list if q['status'] == "대기중"]
            
            if not pending_questions:
                st.write("✅ 현재 답변을 기다리는 질문이 없습니다.")
            else:
                for i, q in enumerate(st.session_state.qna_list):
                    if q['status'] == "대기중":
                        with st.container():
                            st.write(f"**질문:** {q['title']}")
                            # 고유한 key 값을 위해 인덱스(i) 사용
                            answer_text = st.text_area("답변 작성란", key=f"ans_{i}")
                            
                            if st.button("답변 완료 및 등록", key=f"btn_{i}"):
                                if answer_text:
                                    st.session_state.qna_list[i]['answer'] = answer_text
                                    st.session_state.qna_list[i]['status'] = "답변완료" # 상태 업데이트
                                    st.rerun()
                                else:
                                    st.warning("답변 내용을 입력해주세요.")
        elif admin_pw:
            st.error("비밀번호가 일치하지 않습니다.")

# --- 사이트맵 화면 ---
elif st.session_state.current_page == "sitemap":
    st.title("🗺️ 플랫폼 사이트맵")
    st.info("현재 웹사이트의 전체 구조를 한눈에 파악할 수 있습니다.")
    st.divider()
    
    st.markdown("""
    ### 🏠 메인 화면
    * **1️⃣ AI 규제 검토 & 지도 시뮬레이션** (AI 심층 분석 및 카카오 지도 연동)
    * **2️⃣ 민원 양식 생성** (행정 서류 자동 완성 - 준비 중)
    
    ### 💡 게시판 및 안내
    * **Q&A 게시판** (FAQ 및 사용자 질의응답)
    * **사이트맵** (전체 구조 안내)
    
    ### ⚙️ 제어 패널 (사이드바)
    * 화면 테마 변경 (다크/라이트 모드)
    * 새로운 분석 시작
    * 과거 분석 기록 열람 및 삭제
    """)
