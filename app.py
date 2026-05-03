import streamlit as st
import time
from datetime import datetime
import traceback
import streamlit.components.v1 as components 
import pandas as pd
import numpy as np
import base64
import os

# [구조 분리] 백엔드 통합 프로세서
from processor import handle_ai_analysis 
from style import apply_custom_style
from components import render_user_message, render_ai_report
from storage import load_history, save_history 

# --- [로컬 이미지 변환 함수] 이미지가 깨지지 않도록 Base64로 인코딩 ---
def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

# 1. 페이지 설정 (최상단)
st.set_page_config(page_title="용인시 건축 조례 지원 플랫폼", layout="wide")

# 2. 상태 변수 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_history()
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "dark_mode_toggle" not in st.session_state:
    st.session_state.dark_mode_toggle = st.session_state.dark_mode
def sync_dark_mode():
    """토글 버튼 값을 실제 다크모드 상태에 저장합니다."""
    st.session_state.dark_mode = st.session_state.dark_mode_toggle
if "selected_index" not in st.session_state:
    st.session_state.selected_index = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "main"
if "qna_list" not in st.session_state:
    st.session_state.qna_list = [] 

# 3. 스타일 적용
apply_custom_style(st.session_state.dark_mode)

# 🚨 [신규 추가] 다크모드 시 흰색 텍스트/흰색 배경 겹침 현상 및 버튼 글씨 안보임 해결을 위한 CSS 패치
if st.session_state.dark_mode:
    st.markdown("""
    <style>
        /* 다크모드: 아코디언(Expander) 및 입력창 배경을 어둡게, 글자는 하얗게 강제 지정 */
        div[data-testid="stExpander"] details summary {
            background-color: #262730 !important;
            color: #ffffff !important;
        }
        div[data-testid="stExpander"] details summary p {
            color: #ffffff !important;
        }
        div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div {
            background-color: #262730 !important;
        }
        input, textarea {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }
        
        /* 🚨 추가: 다크모드 폼 제출 버튼 및 일반 버튼 가시성 확보 */
        div[data-testid="stFormSubmitButton"] button, 
        div[data-testid="stButton"] button {
            background-color: #333333 !important;
            color: #ffffff !important;
            border: 1px solid #555555 !important;
        }
        div[data-testid="stFormSubmitButton"] button p, 
        div[data-testid="stButton"] button p {
            color: #ffffff !important;
        }
        div[data-testid="stFormSubmitButton"] button:hover, 
        div[data-testid="stButton"] button:hover {
            background-color: #444444 !important;
            border: 1px solid #ffffff !important;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        /* 라이트모드: 정상적인 검은색 글자 강제 지정 */
        div[data-testid="stExpander"] details summary p, input, textarea {
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
        }
        /* 라이트모드 버튼 강제 지정 (다크모드 토글 대비) */
        div[data-testid="stFormSubmitButton"] button p, 
        div[data-testid="stButton"] button p {
            color: #000000 !important;
        }
    </style>
    """, unsafe_allow_html=True)

# 4. 사이드바 구성
with st.sidebar:
    st.title("⚙️ 플랫폼 제어")
    
    st.subheader("📌 메뉴")
    
    if st.button("🏠 메인화면 (챗봇)", use_container_width=True):
        st.session_state.current_page = "main"
        st.rerun()
    if st.button("📝 민원 양식 생성", use_container_width=True):
        st.session_state.current_page = "doc_gen"
        st.rerun()
    if st.button("🗺️ 대지 위치 시각화", use_container_width=True):
        st.session_state.current_page = "map"
        st.rerun()
    if st.button("💡 Q&A 게시판", use_container_width=True):
        st.session_state.current_page = "qna"
        st.rerun()
    if st.button("🗺️ 사이트맵", use_container_width=True):
        st.session_state.current_page = "sitemap"
        st.rerun()

    st.toggle(
    "🌙 다크 모드",
    key="dark_mode_toggle",
    on_change=sync_dark_mode
)
    
    st.divider()
    if st.button("➕ 새 대화 시작", use_container_width=True, type="primary"):
        st.session_state.selected_index = None
        st.session_state.current_page = "main"
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
                st.session_state.current_page = "main"
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


# ==========================================
# 5. 화면 분기 처리
# ==========================================

# --- 🏠 1. 메인화면 (소개 + 챗봇 단독) ---
if st.session_state.current_page == "main":
    st.title("🏢 건축 조례 및 법령 해석 지원 플랫폼")

    with st.container():
       st.info("""
    **⚡ 용인시 건축 법규·조례 통합 분석 AI 플랫폼**
    
    건축사, 시공사, 인허가 담당자의 빠르고 정확한 의사결정을 지원하는 전문가 전용 솔루션입니다.
    
    * **데이터 통합:** 경기도 및 용인시 조례, 상위 법령 등 125개 핵심 규제 데이터베이스화
    * **AI 심층 분석:** 검색을 통한 연관 법규 교차 검증 및 해석 제공
    * **리스크 최소화:** 법규 해석 오류 방지 및 신속·정확한 행정 처리 지원
    """)
    st.write("") 

    st.subheader("🤖 법규 규제 검토 및 질의응답 (챗봇)")
    
    chat_box = st.container(height=550, border=False)
    user_query = st.chat_input("분석이 필요한 건축 규제를 입력해 주세요")
    
    with chat_box:
        if st.session_state.selected_index is not None:
            idx = st.session_state.selected_index
            selected_chat = st.session_state.chat_history[idx]
            st.success(f"📅 과거 분석 기록 열람 중 (조회 일시: {selected_chat.get('time', '')})")
            render_user_message(selected_chat["query"])
            render_ai_report(selected_chat["response"])
            
            if st.button("닫기 및 새 질문하기", use_container_width=True):
                st.session_state.selected_index = None
                st.rerun()
        else:
            for chat in st.session_state.chat_history:
                render_user_message(chat["query"])
                render_ai_report(chat["response"])

        if user_query:
            render_user_message(user_query)
            with st.status("🔍 심층 분석 진행 중...", expanded=True) as status:
                try:
                    st.write("🛰️ 법률 시맨틱 레이어 및 통합 엔진 가동 중...")
                    response_text = handle_ai_analysis(user_query)
                    status.update(label="✅ 분석 완료", state="complete")
                    render_ai_report(response_text)
                except Exception as e:
                    status.update(label="❌ 시스템 에러 발생", state="error")
                    st.error(f"오류가 발생했습니다: {str(e)}")
                    with st.expander("상세 에러 내용"):
                        st.code(traceback.format_exc())
            st.rerun()


# --- 📝 2. 민원 양식 생성 ---
elif st.session_state.current_page == "doc_gen":
    st.title("📝 민원 양식 생성")
    st.write("")
    st.warning("🚧 행정 민원 지원 기능 준비 중")


# --- 🗺️ 3. 대지 위치 시각화 (독립된 지도 페이지) ---
elif st.session_state.current_page == "map":
    st.title("🗺️ 대지 위치 및 건축선 시각화")
    st.write("카카오 지도를 통해 대지 위치 및 주변 환경을 확인합니다.")
    st.write("")
    
    KAKAO_JS_KEY = "본인의_카카오_자바스크립트_앱_키를_여기에_붙여넣으세요"
    map_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            #map {{ width: 100%; height: 650px; border-radius: 12px; border: 1px solid #eaeaea; }}
        </style>
    </head>
    <body>
        <div id="map"></div>
        <script type="text/javascript" src="//dapi.kakao.com/v2/maps/sdk.js?appkey={KAKAO_JS_KEY}"></script>
        <script>
            var mapContainer = document.getElementById('map'); 
            var mapOption = {{ center: new kakao.maps.LatLng(37.241086, 127.177553), level: 4 }};
            var map = new kakao.maps.Map(mapContainer, mapOption);
            map.addControl(new kakao.maps.MapTypeControl(), kakao.maps.ControlPosition.TOPRIGHT);
            map.addControl(new kakao.maps.ZoomControl(), kakao.maps.ControlPosition.RIGHT);
            map.addOverlayMapTypeId(kakao.maps.MapTypeId.USE_DISTRICT);
        </script>
    </body>
    </html>
    """
    if KAKAO_JS_KEY == "본인의_카카오_자바스크립트_앱_키를_여기에_붙여넣으세요":
        st.warning("🚧 카카오 JavaScript API 키를 코드에 입력해 주세요.")
    else:
        components.html(map_html, height=670)


# --- 💡 4. Q&A 게시판 (관리자 기능 복구) ---
elif st.session_state.current_page == "qna":
    st.title("💡 자주 묻는 질문 (FAQ) 및 Q&A")
    st.write("플랫폼 사용법 및 건축 법령 해석과 관련된 질문을 확인하고 남길 수 있습니다.")
    st.divider()
    
    st.subheader("📌 자주 묻는 질문 (기본 예시)")
    with st.expander("ex) 이 플랫폼은 어떤 데이터를 바탕으로 답변하나요?"):
        st.write("A. 용인시/경기도 건축 조례 및 125개 상위 법령 데이터를 통합하여 답변합니다.")
    with st.expander("ex) 과거 분석 기록은 어떻게 확인하나요?"):
        st.write("A. 좌측 사이드바의 '대화 이력'에서 클릭하여 열람할 수 있습니다.")

    st.divider()
    st.subheader("📋 사용자 질문 목록")
    if len(st.session_state.qna_list) == 0:
        st.caption("아직 등록된 질문이 없습니다.")
    else:
        for i, q in enumerate(st.session_state.qna_list):
            status_badge = "🔴 대기중" if q['status'] == "대기중" else "🟢 답변완료"
            with st.expander(f"[{status_badge}] {q['title']}"):
                st.write(f"**Q. {q['content']}**")
                if q['status'] == "답변완료":
                    st.info(f"**A. {q['answer']}**")

    st.divider()
    st.subheader("📝 새로운 질문 남기기")
    with st.form("qna_form", clear_on_submit=True):
        q_title = st.text_input("질문 제목")
        q_content = st.text_area("질문 내용 (구체적으로 작성해주세요)")
        if st.form_submit_button("질문 등록하기"):
            if q_title and q_content:
                new_question = {"title": q_title, "content": q_content, "status": "대기중", "answer": ""}
                st.session_state.qna_list.append(new_question)
                st.success("질문이 성공적으로 등록되었습니다! 관리자 확인 후 답변이 달립니다.")
                st.rerun()
            else:
                st.error("제목과 내용을 모두 입력해 주세요.")

    st.divider()
    
    # 🚨 [복구된 부분] 관리자 메뉴 (답변 달기 기능)
    st.subheader("🛠️ 관리자 메뉴 (답변 달기)")
    if st.toggle("관리자 모드 켜기"):
        admin_pw = st.text_input("관리자 비밀번호 입력", type="password")
        if admin_pw == "2026":
            st.success("관리자 인증 완료! 대기중인 질문에 답변을 달아주세요.")
            pending_questions = [q for q in st.session_state.qna_list if q['status'] == "대기중"]
            if not pending_questions:
                st.write("✅ 현재 답변을 기다리는 질문이 없습니다.")
            else:
                for i, q in enumerate(st.session_state.qna_list):
                    if q['status'] == "대기중":
                        with st.container():
                            st.write(f"**질문:** {q['title']}")
                            answer_text = st.text_area("답변 작성란", key=f"ans_{i}")
                            if st.button("답변 완료 및 등록", key=f"btn_{i}"):
                                if answer_text:
                                    st.session_state.qna_list[i]['answer'] = answer_text
                                    st.session_state.qna_list[i]['status'] = "답변완료"
                                    st.rerun()
                                else:
                                    st.warning("답변 내용을 입력해주세요.")
        elif admin_pw:
            st.error("비밀번호가 일치하지 않습니다.")


# --- 🗺️ 5. 사이트맵 (로컬 이미지 Base64 인코딩 적용) ---
elif st.session_state.current_page == "sitemap":
    st.title("🗺️ 플랫폼 시스템 아키텍처 및 사이트맵")
    st.info("용인시 건축 조례 전문 해석 AI 플랫폼의 전체 구조와 취급 법규 목록입니다.")
    st.write("")

    # 로컬 이미지 경로 지정 (app.py 기준 상대 경로)
    moleg_path = "images/moleg_logo.png" 
    kakao_path = "images/kakao_logo.png"

    # 이미지 파일을 Base64 문자열로 변환
    moleg_base64 = get_image_base64(moleg_path)
    kakao_base64 = get_image_base64(kakao_path)

    # HTML에 주입할 데이터 URI 생성
    moleg_src = f"data:image/png;base64,{moleg_base64}" if moleg_base64 else ""
    kakao_src = f"data:image/png;base64,{kakao_base64}" if kakao_base64 else ""
    
    architecture_html = f"""
    <style>
        .arch-container {{ background-color: #0b459c; padding: 20px; border-radius: 12px; font-family: 'Malgun Gothic', sans-serif; color: #333; }}
        .arch-title {{ text-align: center; color: white; font-size: 22px; font-weight: bold; margin-bottom: 20px; }}
        .arch-layer {{ background-color: white; border-radius: 8px; padding: 15px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .layer-title {{ text-align: center; font-weight: bold; color: #0b459c; margin-bottom: 10px; font-size: 17px; border-bottom: 2px solid #f0f2f6; padding-bottom: 5px; }}
        .box-row {{ display: flex; justify-content: space-between; gap: 10px; }}
        .arch-box {{ flex: 1; background-color: #e6f0fa; border: 1px solid #c1d5ea; border-radius: 6px; padding: 12px; text-align: center; font-size: 13px; font-weight: 600; }}
        .arch-box span {{ display: block; font-size: 11px; font-weight: normal; color: #555; margin-top: 4px; }}
        .data-source-row {{ display: flex; justify-content: center; gap: 15px; margin-top: 10px; }}
        .data-source {{ display: flex; align-items: center; justify-content: center; background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 30px; padding: 8px 18px; font-size: 13px; font-weight: bold; color: #495057; box-shadow: 0 2px 4px rgba(0,0,0,0.05); gap: 8px; }}
        
        .custom-icon {{ height: 20px; object-fit: contain; margin-right: 4px; }}
        .kakao-icon {{ height: 20px; object-fit: contain; margin-right: 4px; background-color: #fae100; border-radius: 4px; padding: 2px; }}
        .emoji-icon {{ font-size: 18px; margin-right: 4px; }}
    </style>

    <div class="arch-container">
        <div class="arch-title">용인시 건축 조례 전문 해석 AI 플랫폼 사이트맵</div>
        
        <div class="arch-layer">
            <div class="layer-title">대국민 / 실무자 서비스 (UI)</div>
            <div class="box-row">
                <div class="arch-box">🤖 AI 건축 규제 검토<span>(법령 시맨틱 분석 질의응답)</span></div>
                <div class="arch-box">🗺️ 대지 위치 시각화<span>(카카오 지도 및 건축선 확인)</span></div>
                <div class="arch-box">📝 민원 양식 생성<span>(행정 서류 자동 완성)</span></div>
                <div class="arch-box">💡 Q&A 게시판<span>(자주 묻는 질문 및 사용자 커뮤니티)</span></div>
            </div>
        </div>

        <div class="arch-layer">
            <div class="layer-title">AI 및 백엔드 통합 엔진 (Legal Module)</div>
            <div class="box-row">
                <div class="arch-box">LLM 분석 엔진<span>(handle_ai_analysis)</span></div>
                <div class="arch-box">법률 레이어링<span>(규제 조항 필터링 및 매핑)</span></div>
                <div class="arch-box">세션 관리자<span>(대화 이력 및 Q&A 상태 저장)</span></div>
            </div>
        </div>

        <div class="arch-layer">
            <div class="layer-title">외부 시스템 연계 및 DB 구축</div>
            <div class="box-row">
                <div class="arch-box">용인시/경기도 자치법규<span>(지역 조례 7개 데이터)</span></div>
                <div class="arch-box">상위 건축 법령 118개<span>(국가 법령 데이터)</span></div>
                <div class="arch-box">공간 정보 API 연동<span>(지도 및 주소 데이터)</span></div>
            </div>
            
            <div class="data-source-row">
                <div class="data-source">
                    <img class="custom-icon" src="{moleg_src}" alt="법제처" onerror="this.style.display='none'"> 국가법령정보센터
                </div>
                <div class="data-source">
                    <img class="kakao-icon" src="{kakao_src}" alt="카카오맵" onerror="this.style.display='none'"> 카카오맵 API
                </div>
                <div class="data-source">
                    <span class="emoji-icon">🗄️</span> 로컬 DB
                </div>
            </div>
        </div>
    </div>
    """
    components.html(architecture_html, height=520)

    st.divider()

    def make_grid_df(items, cols=3):
        padded_items = items + [""] * ((cols - len(items) % cols) % cols)
        grid = np.array(padded_items).reshape(-1, cols)
        unique_columns = [" " * (i + 1) for i in range(cols)]
        return pd.DataFrame(grid, columns=unique_columns)

    with st.expander("📚 취급 법규 목록 (조례 및 상위 법령)", expanded=True):
        st.write("플랫폼이 분석 가능한 전체 법규 목록입니다. 탭을 클릭하여 종류별로 확인하세요.")
        
        l_tabs = st.tabs(["🏛️ 자치단체 조례", "📜 상위 법령", "🔗 조례 위임 법규 (44개)", "📂 상위법 위임 법규 (61개)"])

        with l_tabs[0]:
            st.markdown("### 🏛️ 경기도 및 용인시 조례 (7개)")
            data_ordinance = [
                ["경기도", "경기도 건축 조례", "건축법"],
                ["경기도", "경기도 건축기본조례", "건축기본법"],
                ["경기도", "경기도 건축물 미술작품 설치 및 관리에 관한 조례", "문화예술진흥법"],
                ["경기도", "경기도 건축물관리 조례", "건축물관리법"],
                ["용인시", "용인시 건축 조례", "건축법"],
                ["용인시", "용인시 건축물관리 조례", "건축물관리법"],
                ["용인시", "용인시 도시계획 조례", "국토의 계획 및 이용에 관한 법률"]
            ]
            df_ord = pd.DataFrame(data_ordinance, columns=["지자체명", "조례명", "위임 법률"])
            st.dataframe(df_ord, hide_index=True, use_container_width=True)

        with l_tabs[1]:
            st.markdown("### 📜 주요 상위 법령 (15개 핵심 법률 외 103개)")
            laws = [
                "건축법 / 시행령 / 시행규칙", "건축기본법 / 시행령", "문화예술진흥법 / 시행령",
                "건축물관리법 / 시행령 / 시행규칙", "국토의 계획 및 이용에 관한 법률 / 시행령 / 시행규칙"
            ]
            for law in laws:
                st.write(f"✔️ {law}")

        with l_tabs[2]:
            st.markdown("### 🔗 조례에서 위임된 하위 법규 (총 44개)")
            sub_laws_1 = [
                "감정평가 및 감정평가사에 관한 법률", "건설기술진흥법", "건축기본법", "건축기본법 시행령", "건축물관리법", 
                "건축물관리법 시행규칙", "건축물관리법 시행령", "건축법", "건축법 시행규칙", "건축법 시행령", "건축사법", 
                "경기도 건축물 미술작품 설치 및 관리에 관한 조례 시행규칙", "경기도 위원회 수당 및 여비 지급 조례", 
                "경기도 지방보조금 관리 조례", "고등교육법", "공공발주사업에 대한 건축사의 업무범위와 대가기준", 
                "공공주택 특별법", "관광진흥법", "국가유산기본법", "국토의 계획 및 이용에 관한 법률", 
                "국토의 계획 및 이용에 관한 법률 시행규칙", "국토의 계획 및 이용에 관한 법률 시행령", 
                "근현대문화유산의 보존 및 활용에 관한 법률", "녹색건축물 조성 지원법", "농지법", "농지법 시행령", 
                "다중이용업소의 안전관리에 관한 특별법 시행령", "대기환경보전법", "도시 및 주거환경정비법", 
                "문화예술진흥법", "문화예술진흥법 시행령", "민간임대주택에 관한 특별법", "민원 처리에 관한 법률 시행령", 
                "산업입지 및 개발에 관한 법률", "산업집적활성화 및 공장설립에 관한 법률", "산지관리법", "실내공기질 관리법", 
                "용인시 각종 위원회 설치 및 운영 조례", "용인시 건축 조례", "용인시 도시계획 조례", "자연공원법", 
                "전통사찰의 보존 및 지원에 관한 법률", "주택법", "한옥 등 건축자산의 진흥에 관한 법률"
            ]
            st.dataframe(make_grid_df(sub_laws_1, 3), hide_index=True, use_container_width=True)

        with l_tabs[3]:
            st.markdown("### 📂 상위법 위임 및 연계 법규 (총 61개)")
            sub_laws_2 = [
                "건설기술 진흥법", "건설기술 진흥법 시행령", "건설산업기본법", "건축기본법", "건축법", "건축법 시행령", 
                "건축사법", "경관법", "고등교육법", "공간정보의 구축 및 관리 등에 관한 법률", "공공기관의 운영에 관한 법률", 
                "공공주택 특별법", "공동주택관리법", "공유재산 및 물품 관리법", "공익사업을 위한 토지 등의 취득 및 보상에 관한 법률", 
                "관광진흥법", "국가기술자격법", "국가유산기본법", "국유재산법", "국토안전관리원법", "국토의 계획 및 이용에 관한 법률", 
                "국토의 계획 및 이용에 관한 법률 시행령", "기술사법", "녹색건축물 조성 지원법", "농어촌정비법", "농지법", "도로법", 
                "도시 및 주거환경정비법", "도시개발법", "도시공원 및 녹지 등에 관한 법률", "도시교통정비 촉진법", 
                "도시재생 활성화 및 지원에 관한 특별법", "문화예술진흥법", "문화유산의 보존 및 활용에 관한 법률", "민법", 
                "빈집 및 소규모주택 정비에 관한 특례법", "사도법", "산림자원의 조성 및 관리에 관한 법률", "산업입지 및 개발에 관한 법률", 
                "산업집적활성화 및 공장설립에 관한 법률", "산지관리법", "소방시설 설치 및 관리에 관한 법률", "수도권정비계획법", 
                "수도법", "수산자원관리법 시행령", "시설물의 안전 및 유지관리에 관한 특별법", "영유아보육법", "자연공원법", 
                "자연유산의 보존 및 활용에 관한 법률", "자연재해대책법", "전자정부법", "주차장법", "주택법", "지방공기업법", 
                "집합건물의 소유 및 관리에 관한 법률", "택지개발촉진법", "토지이용규제 기본법", "하수도법", "하천법", 
                "한국토지주택공사법", "행정대집행법"
            ]
            st.dataframe(make_grid_df(sub_laws_2, 3), hide_index=True, use_container_width=True)
