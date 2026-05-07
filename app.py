import streamlit as st
import time
from datetime import datetime
import traceback
import streamlit.components.v1 as components 
import pandas as pd
import numpy as np
import base64
import os
import io
from docx import Document  # [최적화] 조건문 내부의 import를 최상단으로 이동

# [구조 분리] 백엔드 통합 프로세서
from processor import handle_ai_analysis, generate_civil_document # generate_civil_document 추가
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
    st.session_state.dark_mode = st.session_state.dark_mode_toggle
if "selected_index" not in st.session_state:
    st.session_state.selected_index = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "main"
if "qna_list" not in st.session_state:
    st.session_state.qna_list = [] 

# 3. 스타일 적용
apply_custom_style(st.session_state.dark_mode)

# [CSS 패치 생략 없이 원본 유지]
if st.session_state.dark_mode:
    st.markdown("""
    <style>
        div[data-testid="stExpander"] details summary { background-color: #262730 !important; color: #ffffff !important; }
        div[data-testid="stExpander"] details summary p { color: #ffffff !important; }
        div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div { background-color: #262730 !important; }
        input, textarea { color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; }
        div[data-testid="stFormSubmitButton"] button, div[data-testid="stButton"] button {
            background-color: #333333 !important; color: #ffffff !important; border: 1px solid #555555 !important;
        }
        div[data-testid="stFormSubmitButton"] button p, div[data-testid="stButton"] button p { color: #ffffff !important; }
        div[data-testid="stFormSubmitButton"] button:hover, div[data-testid="stButton"] button:hover {
            background-color: #444444 !important; border: 1px solid #ffffff !important;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        div[data-testid="stExpander"] details summary p, input, textarea { color: #000000 !important; -webkit-text-fill-color: #000000 !important; }
        div[data-testid="stFormSubmitButton"] button p, div[data-testid="stButton"] button p { color: #000000 !important; }
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

    st.toggle("🌙 다크 모드", key="dark_mode_toggle", on_change=sync_dark_mode)
    
    st.divider()
    if st.button("➕ 새 대화 시작", use_container_width=True):
        st.session_state.selected_index = None
        st.session_state.current_page = "main"
        st.rerun()
        
    st.divider()
    st.subheader("📁 대화 이력 (클릭 시 열람)")
    
    if st.session_state.chat_history:
        for i, chat in enumerate(reversed(st.session_state.chat_history)):
            actual_index = len(st.session_state.chat_history) - 1 - i
            time_str = chat.get("updated_at", chat.get("created_at", "00:00:00"))[11:16]
            query_summary = chat.get("title", "새 대화")
            if len(query_summary) > 12: query_summary = query_summary[:12] + "..."
            
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
    건축사, 시공사, 인허가 담당자의 빠르고 정확한 의사결정을 지원하는 전문가 전용 솔루션입니다.
    * **조례 데이터 취급:** 경기도 및 용인시 조례, 상위 법령 등 125개 핵심 규제 데이터베이스화
    * **AI 심층 분석:** 검색을 통한 연관 법규 교차 검증 및 해석 제공
    * **리스크 방지:** 법규 해석 오류 방지 및 신속·정확한 행정 처리 지원
    """)
    st.write("") 

    st.subheader("🤖 법규 규제 검토 및 질의응답 (챗봇)")
    
    chat_box = st.container(height=550, border=False)
    user_query = st.chat_input("분석이 필요한 건축 규제를 입력해 주세요")
    
    with chat_box:
        if st.session_state.selected_index is not None:
            idx = st.session_state.selected_index
            selected_chat = st.session_state.chat_history[idx]
            st.success(f"📅 대화방 열람 중: {selected_chat.get('title', '새 대화')}")
            
            for msg in selected_chat.get("messages", []):
                render_user_message(msg.get("query", ""))
                render_ai_report(msg.get("response", ""))
            
            if st.button("닫기 및 새 질문하기", use_container_width=True):
                st.session_state.selected_index = None
                st.rerun()
        else:
            st.info("새 대화를 시작하려면 아래 입력창에 질문을 입력하세요.")

        if user_query:
            render_user_message(user_query)
            with st.status("🔍 심층 분석 진행 중...", expanded=True) as status:
                try:
                    st.write("🛰️ 법률 시맨틱 레이어 및 통합 엔진 가동 중...")
                    response_text = handle_ai_analysis(user_query)
                    
                    if st.session_state.chat_history:
                        st.session_state.selected_index = len(st.session_state.chat_history) - 1
                    
                    status.update(label="✅ 분석 완료", state="complete")
                    render_ai_report(response_text)
                except Exception as e:
                    status.update(label="❌ 시스템 에러 발생", state="error")
                    st.error(f"오류가 발생했습니다: {str(e)}")
                    with st.expander("상세 에러 내용"):
                        st.code(traceback.format_exc())
            st.rerun()


# --- 📝 2. 민원 양식 생성 (개선 및 최적화 반영) ---
elif st.session_state.current_page == "doc_gen":
    st.title("📝 용인시 맞춤형 건축 민원 양식 생성")

    # [개선 1, 3] 용인시 한정 및 법적 검토 배제 문구 적용
    st.info("""
    용인시 관내 건축 관련 민원을 입력하면 다음을 지원합니다:

    ✔️ AI 기반 민원서 자동 완성 (양식 작성에 집중)
    ✔️ 민원별 필요 서류 안내
    ✔️ 용인시 맞춤형 접수 절차 안내
    ✔️ 민원 처리 상태 조회 안내
    
    ※ 법령 해석 및 규제 검토가 필요하신 경우 '메인화면(챗봇)'을 이용해 주세요.
    """)
    st.divider()

    # [최적화] 구조체 외부 분리를 통한 반복 렌더링 방지 및 유지보수 향상
    required_docs = {
        "건축허가 관련": ["건축허가 신청서", "배치도", "평면도", "토지이용계획확인서", "건축계획서"],
        "건축선 문의": ["대지 위치도", "토지이용계획확인서", "현장 사진"],
        "일조권 민원": ["현장 사진", "건축물 배치도", "피해 설명 자료"],
        "불법건축물 신고": ["현장 사진", "위치도", "불법사항 설명자료"],
        "용도변경 문의": ["건축물대장", "평면도", "용도변경 계획서"],
        "주차장 기준 문의": ["배치도", "주차계획도", "건축 개요"],
        "건축물 해석 문의": ["질의서", "관련 도면", "현장 사진"],
        "기타": ["신분증", "민원 설명자료"]
    }

    department_map = {
        "건축허가 관련": "건축허가과",
        "건축선 문의": "건축과",
        "일조권 민원": "건축과",
        "불법건축물 신고": "건축과",
        "용도변경 문의": "건축허가과",
        "주차장 기준 문의": "교통정책과",
        "건축물 해석 문의": "건축과",
        "기타": "민원여권과"
    }

    # 1. 민원 유형 선택 (하드코딩 제거)
    civil_type = st.selectbox("📌 민원 유형 선택", list(required_docs.keys()))

    # 2. 주소 입력
    site_address = st.text_input(
        "📍 대상 건축물 주소",
        placeholder="예: 경기도 용인시 처인구 ..."
    )

    # 3. 민원 내용 입력
    civil_content = st.text_area(
        "✏️ 민원 내용을 상세히 입력해주세요",
        height=250,
        placeholder="예: 인접 대지 건축물로 인해 일조권 침해가 발생하고 있습니다..."
    )

    st.divider()

    # 4. 민원 생성 버튼
    if st.button("📄 AI 민원 양식 생성", use_container_width=True):
        if not site_address or not civil_content:
            st.error("주소와 민원 내용을 모두 입력해주세요.")
        else:
            with st.status("🔍 민원서 생성 중...", expanded=True) as status:
                try:
                    st.write("🛰️ 서식 구조화 및 양식 작성 중...")
                    
                    # [개선 5] 메인화면 챗봇 이력 노출 분리
                    # 주의: 백엔드 processor.py의 generate_civil_document 내부에 history 저장 로직이 있다면 분리 필요
                    # 예: result = generate_civil_document(civil_type, site_address, civil_content, save_history=False)
                    result = generate_civil_document(
                        civil_type,
                        site_address,
                        civil_content
                    )

                    status.update(label="✅ 민원서 생성 완료", state="complete")
                    st.success("민원서 생성이 완료되었습니다.")

                    # --- 생성 결과 출력 ---
                    st.subheader("📄 생성된 민원서")
                    st.markdown(result)
                    st.divider()

                    # --- 필요 서류 안내 ---
                    st.subheader("📎 민원 접수 시 필요 서류")
                    docs = required_docs.get(civil_type, required_docs["기타"])
                    for doc in docs:
                        st.write(f"✔️ {doc}")
                    st.divider()

                    # --- 담당 부서 안내 ---
                    dept = department_map.get(civil_type, "민원여권과")
                    st.subheader("🏢 예상 담당 부서")
                    st.info(f"📌 추천 담당 부서: 용인시 {dept} (또는 각 구청 {dept})")
                    st.divider()

                    # --- [개선 2, 4] 접수 절차 구체화 및 직관적인 링크 배치 ---
                    st.subheader("🏛️ 용인시 민원 접수 절차 안내")

                    st.markdown("""
                    ### ✅ 온라인 접수
                    * **[🔗 정부24 (gov.kr)](https://www.gov.kr)**
                      : 로그인 ➔ 민원신청 ➔ '건축' 검색 ➔ 해당 서식 작성 및 파일 첨부 ➔ 신청 완료
                    * **[🔗 국민신문고 (epeople.go.kr)](https://www.epeople.go.kr)**
                      : 로그인 ➔ 민원신청 ➔ 생성된 본문 복사/붙여넣기 ➔ 처리기관을 **'용인시'**로 지정 ➔ 신청 완료
                    * **[🔗 용인시청 홈페이지 (yongin.go.kr)](https://www.yongin.go.kr)**
                      : 로그인 ➔ 시민참여 ➔ 종합민원 ➔ 민원신청 게시판 등록

                    ### ✅ 방문(오프라인) 접수
                    * **접수처**: 용인시청 종합민원실 및 각 구청(처인구, 기흥구, 수지구) 건축허가과 민원창구
                    * **절 차**: 신분증 및 필요 서류(출력물) 지참 ➔ 방문 ➔ 번호표 발급 대기 ➔ 담당자 서류 제출 및 접수증 수령

                    ### ✅ 전화 사전 문의
                    * **용인시 민원콜센터 (☎️ 1577-1122)**
                      : 방문 전 부서 연결 및 기본 서류, 접수 가능 여부 사전 안내
                    """)
                    st.divider()

                    # --- 민원 조회 방법 ---
                    st.subheader("🔍 민원 처리 상태 조회")
                    st.success("""
                    접수 후 아래 경로에서 처리 현황을 확인할 수 있습니다.
                    
                    ✔️ **정부24** ➔ MyGOV ➔ 나의 신청내역
                    ✔️ **국민신문고** ➔ 나의 민원 ➔ 나의 민원결과
                    ✔️ **용인시청** ➔ 전자민원 ➔ 나의 민원 조회
                    """)
                    st.divider()

                    # --- DOCX 다운로드 ---
                    st.subheader("📥 민원서 다운로드")
                    doc = Document()
                    doc.add_heading('용인시 건축 행정 민원서', level=1)
                    doc.add_paragraph(f"민원 유형: {civil_type}")
                    doc.add_paragraph(f"대상 주소: {site_address}")
                    doc.add_heading('민원 내용', level=2)
                    doc.add_paragraph(result)

                    buffer = io.BytesIO()
                    doc.save(buffer)
                    buffer.seek(0)

                    st.download_button(
                        label="📄 DOCX 민원서 다운로드",
                        data=buffer,
                        file_name="용인시_건축민원서.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )

                except Exception as e:
                    status.update(label="❌ 민원 생성 실패", state="error")
                    st.error(f"오류 발생: {str(e)}")
                    with st.expander("상세 오류"):
                        st.code(traceback.format_exc())


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


# --- 🗺️ 5. 사이트맵 (이하 원본과 동일) ---
elif st.session_state.current_page == "sitemap":
    st.title("🗺️ 플랫폼 시스템 아키텍처 및 사이트맵")
    st.info("용인시 건축 조례 전문 해석 AI 플랫폼의 전체 구조와 취급 법규 목록입니다.")
    st.write("")
    
    moleg_path = "images/moleg_logo.png" 
    kakao_path = "images/kakao_logo.png"
    moleg_base64 = get_image_base64(moleg_path)
    kakao_base64 = get_image_base64(kakao_path)

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
            sub_laws_1 = ["감정평가 및 감정평가사에 관한 법률", "건설기술진흥법", "건축기본법", "건축기본법 시행령", "건축물관리법", "건축물관리법 시행규칙", "건축물관리법 시행령", "건축법", "건축법 시행규칙", "건축법 시행령", "건축사법", "경기도 건축물 미술작품 설치 및 관리에 관한 조례 시행규칙", "경기도 위원회 수당 및 여비 지급 조례", "경기도 지방보조금 관리 조례", "고등교육법", "공공발주사업에 대한 건축사의 업무범위와 대가기준", "공공주택 특별법", "관광진흥법", "국가유산기본법", "국토의 계획 및 이용에 관한 법률", "국토의 계획 및 이용에 관한 법률 시행규칙", "국토의 계획 및 이용에 관한 법률 시행령", "근현대문화유산의 보존 및 활용에 관한 법률", "녹색건축물 조성 지원법", "농지법", "농지법 시행령", "다중이용업소의 안전관리에 관한 특별법 시행령", "대기환경보전법", "도시 및 주거환경정비법", "문화예술진흥법", "문화예술진흥법 시행령", "민간임대주택에 관한 특별법", "민원 처리에 관한 법률 시행령", "산업입지 및 개발에 관한 법률", "산업집적활성화 및 공장설립에 관한 법률", "산지관리법", "실내공기질 관리법", "용인시 각종 위원회 설치 및 운영 조례", "용인시 건축 조례", "용인시 도시계획 조례", "자연공원법", "전통사찰의 보존 및 지원에 관한 법률", "주택법", "한옥 등 건축자산의 진흥에 관한 법률"]
            st.dataframe(make_grid_df(sub_laws_1, 3), hide_index=True, use_container_width=True)

        with l_tabs[3]:
            st.markdown("### 📂 상위법 위임 및 연계 법규 (총 61개)")
            sub_laws_2 = ["건설기술 진흥법", "건설기술 진흥법 시행령", "건설산업기본법", "건축기본법", "건축법", "건축법 시행령", "건축사법", "경관법", "고등교육법", "공간정보의 구축 및 관리 등에 관한 법률", "공공기관의 운영에 관한 법률", "공공주택 특별법", "공동주택관리법", "공유재산 및 물품 관리법", "공익사업을 위한 토지 등의 취득 및 보상에 관한 법률", "관광진흥법", "국가기술자격법", "국가유산기본법", "국유재산법", "국토안전관리원법", "국토의 계획 및 이용에 관한 법률", "국토의 계획 및 이용에 관한 법률 시행령", "기술사법", "녹색건축물 조성 지원법", "농어촌정비법", "농지법", "도로법", "도시 및 주거환경정비법", "도시개발법", "도시공원 및 녹지 등에 관한 법률", "도시교통정비 촉진법", "도시재생 활성화 및 지원에 관한 특별법", "문화예술진흥법", "문화유산의 보존 및 활용에 관한 법률", "민법", "빈집 및 소규모주택 정비에 관한 특례법", "사도법", "산림자원의 조성 및 관리에 관한 법률", "산업입지 및 개발에 관한 법률", "산업집적활성화 및 공장설립에 관한 법률", "산지관리법", "소방시설 설치 및 관리에 관한 법률", "수도권정비계획법", "수도법", "수산자원관리법 시행령", "시설물의 안전 및 유지관리에 관한 특별법", "영유아보육법", "자연공원법", "자연유산의 보존 및 활용에 관한 법률", "자연재해대책법", "전자정부법", "주차장법", "주택법", "지방공기업법", "집합건물의 소유 및 관리에 관한 법률", "택지개발촉진법", "토지이용규제 기본법", "하수도법", "하천법", "한국토지주택공사법", "행정대집행법"]
            st.dataframe(make_grid_df(sub_laws_2, 3), hide_index=True, use_container_width=True)
