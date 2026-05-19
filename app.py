import streamlit as st
import time
from datetime import datetime
import traceback
import pandas as pd
import numpy as np
import base64
import os
import io
import uuid

# 1. 페이지 설정 (가장 먼저 실행되어야 함)
st.set_page_config(
    page_title="용인시 건축 조례 지원 플랫폼", 
    page_icon="🏢", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 모듈 Import (페이지 설정 이후)
from widget_utils import inject_floating_button
from docx import Document
from processor import handle_ai_analysis, generate_civil_document
from style import apply_custom_style
from components import render_user_message, render_ai_report
from storage import load_history, save_history 

# 용인시 민원창구 연계버튼
inject_floating_button()

# --- [로컬 이미지 변환 함수] ---
def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

# ==========================================
# 2. 상태 변수 초기화
# ==========================================
if "user_id" not in st.session_state: st.session_state.user_id = "guest"
if "chat_history" not in st.session_state: st.session_state.chat_history = load_history(st.session_state.user_id)
if "dark_mode" not in st.session_state: st.session_state.dark_mode = False
if "selected_index" not in st.session_state: st.session_state.selected_index = None
if "current_page" not in st.session_state: st.session_state.current_page = "main"
if "qna_list" not in st.session_state: st.session_state.qna_list = []

def sync_dark_mode():
    st.session_state.dark_mode = st.session_state.dark_mode_toggle

# ==========================================
# 3. 프리미엄 CSS 스타일링 (SaaS 룩앤필)
# ==========================================
apply_custom_style(st.session_state.dark_mode) # 기존 스타일 함수 호출 유지

def apply_premium_ui(is_dark):
    # 공통 베이스 CSS (Pretendard 폰트, 트랜지션, 버튼 호버 효과)
    base_css = """
<style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    * { font-family: 'Pretendard', sans-serif !important; }
    
    /* 입력창 디자인 */
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div {
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    div[data-baseweb="input"] > div:focus-within, div[data-baseweb="textarea"] > div:focus-within {
        border-color: #0b459c !important;
        box-shadow: 0 0 0 2px rgba(11, 69, 156, 0.2) !important;
    }
    
    /* 버튼 디자인 */
    div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
        border: none !important;
    }
    div[data-testid="stButton"] button:hover, div[data-testid="stFormSubmitButton"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }
    div[data-testid="stButton"] button:active { transform: translateY(0px); }
    
    /* Expander (아코디언 메뉴) 디자인 */
    div[data-testid="stExpander"] {
        border-radius: 10px !important;
        border: 1px solid rgba(150, 150, 150, 0.2) !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03) !important;
        margin-bottom: 12px !important;
    }
</style>
"""
    # 다크/라이트 모드별 색상 세부 조정
    theme_css = """
<style>
    .stApp { background-color: #121212 !important; }
    div[data-testid="stSidebar"] { background-color: #1A1A1D !important; border-right: 1px solid #2d2d30 !important; }
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div { background-color: #242427 !important; border: 1px solid #333 !important; }
    div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button { background-color: #2a2b2f !important; color: #fff !important; }
    div[data-testid="stButton"] button:hover, div[data-testid="stFormSubmitButton"] button:hover { background-color: #3b3d44 !important; }
    div[data-testid="stExpander"] details summary { background-color: #1e1e22 !important; color: #fff !important; }
</style>
""" if is_dark else """
<style>
    .stApp { background-color: #F8F9FA !important; }
    div[data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E9ECEF !important; }
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div { background-color: #FFFFFF !important; border: 1px solid #CED4DA !important; }
    div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button { background-color: #FFFFFF !important; color: #333 !important; border: 1px solid #DEE2E6 !important; box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;}
    div[data-testid="stButton"] button:hover, div[data-testid="stFormSubmitButton"] button:hover { background-color: #F1F3F5 !important; border-color: #CED4DA !important; }
    div[data-testid="stExpander"] details summary { background-color: #FFFFFF !important; color: #212529 !important; }
</style>
"""
    st.markdown(base_css + theme_css, unsafe_allow_html=True)

apply_premium_ui(st.session_state.dark_mode)

# --- [대화기록 검색 팝업] ---
dialog_decorator = st.dialog if hasattr(st, "dialog") else st.experimental_dialog

@dialog_decorator("🔍 대화기록 검색", width="large")
def open_history_search_dialog():
    search_query = st.text_input("검색어 입력", placeholder="예: 일조권, 건폐율...", key="dialog_history_search_input")
    query = search_query.strip().lower()

    if not st.session_state.chat_history:
        st.caption("저장된 대화기록이 없습니다.")
        return

    results = []
    for idx, chat in enumerate(st.session_state.chat_history):
        searchable_text = chat.get("title", "") + " "
        for msg in chat.get("messages", []):
            searchable_text += msg.get("query", "") + " " + msg.get("response", "") + " "
        if not query or query in searchable_text.lower():
            results.append((idx, chat))

    st.caption(f"검색 결과 {len(results)}개" if query else "최근 대화")

    if not results:
        st.warning("검색 결과가 없습니다.")
        return

    with st.container(height=400, border=False):
        for idx, chat in reversed(results[-20:]):
            title = chat.get("title", "새 대화")
            time_str = chat.get("updated_at", chat.get("created_at", ""))
            preview = chat.get("messages", [])[0].get("query", "")[:60] + "..." if chat.get("messages") else ""
            
            with st.container():
                if st.button(f"💬 {title[:25]}... \n\n {time_str}", key=f"dialog_chat_{idx}", use_container_width=True):
                    st.session_state.selected_index = idx
                    st.session_state.current_page = "main"
                    st.rerun()
                st.caption(f"미리보기: {preview}")
                st.markdown("---")

# ==========================================
# 4. 사이드바 구성 (그룹화 및 깔끔한 정리)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2942/2942821.png", width=50) # 로고 예시
    st.title("플랫폼 제어")
    
    # [인증 섹션]
    with st.expander("👤 실무자 시스템 인증", expanded=(st.session_state.user_id == "guest")):
        if st.session_state.user_id == "guest":
            auth_tabs = st.tabs(["로그인", "회원가입"])
            with auth_tabs[0]:
                login_id = st.text_input("아이디", key="login_id")
                login_pw = st.text_input("비밀번호", type="password", key="login_pw")
                if st.button("로그인", use_container_width=True):
                    from storage import authenticate_user
                    if authenticate_user(login_id.strip(), login_pw.strip()):
                        st.session_state.user_id = login_id.strip()
                        st.session_state.chat_history = load_history(st.session_state.user_id)
                        st.toast(f"환영합니다, {st.session_state.user_id}님!", icon="👋")
                        st.rerun()
                    else:
                        st.error("정보가 일치하지 않습니다.")
            with auth_tabs[1]:
                reg_id = st.text_input("새 아이디", key="reg_id")
                reg_pw = st.text_input("비밀번호", type="password", key="reg_pw")
                if st.button("가입하기", use_container_width=True):
                    from storage import check_id_exists, register_user
                    if check_id_exists(reg_id.strip()):
                        st.error("이미 존재하는 아이디입니다.")
                    elif register_user(reg_id.strip(), reg_pw.strip()):
                        st.toast("가입 성공! 로그인해주세요.", icon="✅")
        else:
            st.success(f"현재 접속: **{st.session_state.user_id}**")
            if st.button("안전 로그아웃", use_container_width=True):
                st.session_state.user_id = "guest"
                st.session_state.chat_history = load_history("guest")
                st.session_state.selected_index = None
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    
    # [메뉴 내비게이션]
    st.subheader("📌 메인 메뉴")
    if st.button("🏠 메인화면 (AI 챗봇)", use_container_width=True): st.session_state.current_page = "main"; st.rerun()
    if st.button("📝 민원 양식 자동생성", use_container_width=True): st.session_state.current_page = "doc_gen"; st.rerun()
    if st.button("💡 FAQ & Q&A 게시판", use_container_width=True): st.session_state.current_page = "qna"; st.rerun()
    if st.button("🗺️ 플랫폼 사이트맵", use_container_width=True): st.session_state.current_page = "sitemap"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.toggle("🌙 다크 모드", key="dark_mode_toggle", on_change=sync_dark_mode)
    st.markdown("---")
    
    # [대화 이력 섹션]
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ 새 대화", use_container_width=True):
            st.session_state.selected_index = None
            st.session_state.current_page = "main"
            st.rerun()
    with col2:
        if st.button("🔍 검색", use_container_width=True):
            open_history_search_dialog()

    st.subheader("📁 대화 이력")
    history_container = st.container(height=250, border=True)
    with history_container:
        if st.session_state.chat_history:
            for i, chat in enumerate(reversed(st.session_state.chat_history)):
                actual_index = len(st.session_state.chat_history) - 1 - i
                time_str = chat.get("updated_at", chat.get("created_at", "00-00 00:00"))[5:16]
                query_summary = chat.get("title", "새 대화")[:12] + ".."
                
                if st.button(f"🕒 {time_str} | {query_summary}", key=f"hist_{actual_index}", use_container_width=True):
                    st.session_state.selected_index = actual_index
                    st.session_state.current_page = "main"
                    st.rerun()
        else:
            st.caption("저장된 기록이 없습니다.")

    if st.session_state.chat_history:
        if st.button("🗑️ 전체 기록 삭제", type="primary", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.selected_index = None
            from storage import clear_history
            clear_history(st.session_state.user_id) 
            st.toast("모든 기록이 삭제되었습니다.", icon="🗑️")
            st.rerun()


# ==========================================
# 5. 화면 분기 처리 (Main Content)
# ==========================================

# --- 🏠 1. 메인화면 (챗봇) ---
if st.session_state.current_page == "main":
    st.title("🏢 건축 조례 및 법령 해석 AI")
    st.markdown("<p style='color: #666; font-size: 1.1em;'>건축사, 시공사, 인허가 담당자의 신속한 의사결정을 돕는 심층 규제 분석 엔진입니다.</p>", unsafe_allow_html=True)
    st.write("") 

    chat_box = st.container(height=500, border=False)
    user_query = st.chat_input("예: 용인시 처인구 자연녹지지역의 건폐율과 용적률 기준은?")
    
    with chat_box:
        if st.session_state.selected_index is not None:
            idx = st.session_state.selected_index
            selected_chat = st.session_state.chat_history[idx]
            st.info(f"📅 과거 대화 열람 중: **{selected_chat.get('title', '새 대화')}**")
            
            for msg in selected_chat.get("messages", []):
                render_user_message(msg.get("query", ""))
                render_ai_report(msg.get("response", ""))
            
            if st.button("닫기 및 새 질문하기", use_container_width=True):
                st.session_state.selected_index = None
                st.rerun()
        else:
            # 빈 화면일 때 안내 문구 (Hero Section)
            st.markdown("""
            <div style="text-align:center; padding: 40px; background: rgba(128,128,128,0.05); border-radius: 12px; margin-top: 20px;">
                <h3 style="color: #0b459c;">어떤 규제를 검토해 드릴까요?</h3>
                <p style="color: #666;">경기도/용인시 조례 및 125개 상위 법령 데이터베이스를 기반으로 정확하게 분석합니다.<br>하단의 입력창에 자유롭게 질문을 남겨주세요.</p>
            </div>
            """, unsafe_allow_html=True)

        if user_query:
            render_user_message(user_query)
            with st.status("🔍 법률 시맨틱 엔진 가동 중...", expanded=True) as status:
                try:
                    st.write("🛰️ 조항 필터링 및 교차 검증 진행 중...")
                    response_text = handle_ai_analysis(user_query)
                    
                    if st.session_state.chat_history:
                        st.session_state.selected_index = len(st.session_state.chat_history) - 1
                    
                    status.update(label="✅ 심층 분석 완료", state="complete")
                    render_ai_report(response_text)
                    st.toast("분석이 완료되었습니다.", icon="✨")
                except Exception as e:
                    status.update(label="❌ 시스템 에러 발생", state="error")
                    st.error(f"오류가 발생했습니다: {str(e)}")
            st.rerun()

# --- 📝 2. 민원 양식 생성 ---
elif st.session_state.current_page == "doc_gen":
    st.title("📝 맞춤형 건축 민원 양식 자동완성")
    st.info("💡 **Tip:** 복잡한 민원 내용을 입력하면 AI가 용인시 행정 양식에 맞춰 문서를 정갈하게 작성해 드립니다. (법령 검토는 챗봇을 이용해 주세요)")
    st.divider()

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
        "건축허가 관련": "건축허가과", "건축선 문의": "건축과", "일조권 민원": "건축과", 
        "불법건축물 신고": "건축과", "용도변경 문의": "건축허가과", "주차장 기준 문의": "교통정책과", 
        "건축물 해석 문의": "건축과", "기타": "민원여권과"
    }

    # 레이아웃 개선 (2단 분할)
    col1, col2 = st.columns(2)
    with col1:
        civil_type = st.selectbox("📌 민원 유형 선택", list(required_docs.keys()))
    with col2:
        site_address = st.text_input("📍 대상 건축물 주소", placeholder="예: 경기도 용인시 처인구 중부대로 1199")

    civil_content = st.text_area("✏️ 민원 상세 내용", height=150, placeholder="예: 인접 대지 신축 공사로 인해 심각한 일조권 침해가 우려되어 확인을 요청합니다...")

    if st.button("✨ AI 민원 양식 생성하기", use_container_width=True, type="primary"):
        if not site_address or not civil_content:
            st.error("주소와 민원 내용을 모두 입력해주세요.")
        else:
            with st.spinner("서식 구조화 및 양식 작성 중..."):
                try:
                    result = generate_civil_document(civil_type, site_address, civil_content)
                    st.session_state.selected_index = None # 챗봇 히스토리 충돌 방지
                    st.toast("민원 양식이 성공적으로 생성되었습니다!", icon="🎉")
                    
                    st.divider()
                    st.subheader("📄 생성된 민원서")
                    st.markdown(f"<div style='padding:20px; border:1px solid #ddd; border-radius:8px; background:rgba(0,0,0,0.02);'>{result}</div>", unsafe_allow_html=True)
                    
                    # 정보 안내 탭
                    info_tabs = st.tabs(["📎 필요 서류", "🏢 담당 부서", "🏛️ 접수 절차", "📥 파일 다운로드"])
                    
                    with info_tabs[0]:
                        for doc in required_docs.get(civil_type, required_docs["기타"]):
                            st.write(f"✔️ {doc}")
                    with info_tabs[1]:
                        dept = department_map.get(civil_type, "민원여권과")
                        st.info(f"📌 용인시청 또는 관할 구청 **{dept}** 문의 요망")
                    with info_tabs[2]:
                        st.markdown("""
                        * **온라인:** 정부24(gov.kr), 국민신문고(epeople.go.kr) 용인시 지정 접수
                        * **오프라인:** 용인시청/구청 민원실 방문 접수
                        * **전화문의:** 용인시 민원콜센터 (☎️ 1577-1122)
                        """)
                    with info_tabs[3]:
                        doc = Document()
                        doc.add_heading('용인시 건축 행정 민원서', level=1)
                        doc.add_paragraph(f"민원 유형: {civil_type}\n대상 주소: {site_address}")
                        doc.add_heading('민원 내용', level=2)
                        doc.add_paragraph(result)

                        buffer = io.BytesIO()
                        doc.save(buffer)
                        buffer.seek(0)
                        st.download_button(
                            label="💾 DOCX 양식 다운로드",
                            data=buffer,
                            file_name="용인시_건축민원서.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                except Exception as e:
                    st.error(f"오류 발생: {str(e)}")

# --- 💡 3. Q&A 게시판 ---
elif st.session_state.current_page == "qna":
    st.title("💡 커뮤니티 Q&A")
    st.write("플랫폼 사용법이나 애매한 규제 해석에 대해 질문을 남겨주시면 관리자가 답변해 드립니다.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("📋 실시간 질문 목록")
        if not st.session_state.qna_list:
            st.caption("등록된 질문이 없습니다. 첫 질문의 주인공이 되어보세요!")
        else:
            for i, q in enumerate(st.session_state.qna_list):
                status_badge = "⏳ 답변대기" if q['status'] == "대기중" else "✅ 답변완료"
                with st.expander(f"[{status_badge}] {q['title']}"):
                    st.markdown(f"**Q.** {q['content']}")
                    if q['status'] == "답변완료":
                        st.info(f"**A.** {q['answer']}")
    
    with col2:
        st.subheader("📝 질문 작성하기")
        with st.form("qna_form", clear_on_submit=True):
            q_title = st.text_input("제목", placeholder="질문 요약")
            q_content = st.text_area("내용", placeholder="상세 내용 입력")
            if st.form_submit_button("질문 등록", use_container_width=True):
                if q_title and q_content:
                    st.session_state.qna_list.append({"title": q_title, "content": q_content, "status": "대기중", "answer": ""})
                    st.toast("질문이 등록되었습니다.", icon="✅")
                    st.rerun()
                else:
                    st.error("모두 입력해 주세요.")
        
        st.divider()
        with st.expander("🛠️ 관리자 패널"):
            admin_pw = st.text_input("관리자 PIN", type="password")
            if admin_pw == "2026":
                st.success("인증 완료")
                for i, q in enumerate(st.session_state.qna_list):
                    if q['status'] == "대기중":
                        answer_text = st.text_input(f"답변: {q['title']}", key=f"ans_{i}")
                        if st.button("답변 등록", key=f"btn_{i}"):
                            st.session_state.qna_list[i]['answer'] = answer_text
                            st.session_state.qna_list[i]['status'] = "답변완료"
                            st.rerun()

# --- 🗺️ 4. 사이트맵 ---
elif st.session_state.current_page == "sitemap":
    st.title("🗺️ 시스템 아키텍처 및 취급 데이터")
    st.write("본 플랫폼은 클라우드 기반 AI 엔진과 최신 법률 DB를 연동하여 동작합니다.")
    
    # 아키텍처 다이어그램 HTML 유지하되 CSS만 다듬음
    architecture_html = """
    <style>
        .arch-container { background: linear-gradient(135deg, #0b459c 0%, #1a5fb4 100%); padding: 25px; border-radius: 16px; font-family: 'Pretendard', sans-serif; }
        .arch-title { text-align: center; color: white; font-size: 24px; font-weight: 700; margin-bottom: 25px; letter-spacing: -0.5px; }
        .arch-layer { background-color: rgba(255,255,255,0.95); border-radius: 12px; padding: 20px; margin-bottom: 15px; box-shadow: 0 8px 16px rgba(0,0,0,0.1); }
        .layer-title { text-align: center; font-weight: 800; color: #1a5fb4; margin-bottom: 15px; font-size: 18px; border-bottom: 2px dashed #d1d5db; padding-bottom: 10px; }
        .box-row { display: flex; justify-content: space-between; gap: 15px; }
        .arch-box { flex: 1; background-color: #f0f4f8; border: 1px solid #cbd5e1; border-radius: 8px; padding: 15px; text-align: center; font-size: 14px; font-weight: 700; color: #334155; transition: transform 0.2s; }
        .arch-box:hover { transform: translateY(-3px); background-color: #e2e8f0; }
        .arch-box span { display: block; font-size: 12px; font-weight: 500; color: #64748b; margin-top: 6px; }
        .data-source-row { display: flex; justify-content: center; gap: 20px; margin-top: 15px; }
        .data-source { background-color: white; border: 2px solid #e2e8f0; border-radius: 20px; padding: 8px 20px; font-size: 14px; font-weight: 700; color: #475569; }
    </style>
    <div class="arch-container">
        <div class="arch-title">Legal AI Platform Architecture</div>
        <div class="arch-layer">
            <div class="layer-title">대국민 / 실무자 서비스 (UI Layer)</div>
            <div class="box-row">
                <div class="arch-box">🤖 AI 법률 검토<span>(자연어 질의응답)</span></div>
                <div class="arch-box">📝 자동화 문서 생성<span>(민원양식/행정서류)</span></div>
                <div class="arch-box">💡 커뮤니티<span>(FAQ & Q&A)</span></div>
            </div>
        </div>
        <div class="arch-layer">
            <div class="layer-title">AI 핵심 엔진 (Processing Layer)</div>
            <div class="box-row">
                <div class="arch-box">LLM 분석 모듈<span>(조항 매핑 및 논리 추론)</span></div>
                <div class="arch-box">RAG 검색 시스템<span>(시맨틱 벡터 검색)</span></div>
            </div>
        </div>
        <div class="arch-layer">
            <div class="layer-title">데이터베이스 연동 (Data Layer)</div>
            <div class="box-row">
                <div class="arch-box">용인시/경기도 조례<span>(지역 특화 규제)</span></div>
                <div class="arch-box">국토부 상위 법령<span>(118개 핵심 법률)</span></div>
            </div>
            <div class="data-source-row">
                <div class="data-source">🏛️ 국가법령정보센터 API</div>
                <div class="data-source">🗄️ 플랫폼 로컬 Vector DB</div>
            </div>
        </div>
    </div>
    """
    st.components.v1.html(architecture_html, height=550) if hasattr(st, "components") else st.markdown(architecture_html, unsafe_allow_html=True)
    
    st.divider()
    with st.expander("📚 취급 법규 전체 목록 보기", expanded=True):
        st.caption("※ 탭을 클릭하여 종류별 법규를 확인하세요.")
        tabs = st.tabs(["🏛️ 지역 조례 (7개)", "📜 주요 상위법", "🔗 위임 법규"])
        
        with tabs[0]:
            df_ord = pd.DataFrame([
                ["경기도", "경기도 건축 조례", "건축법"], ["경기도", "경기도 건축기본조례", "건축기본법"],
                ["용인시", "용인시 건축 조례", "건축법"], ["용인시", "용인시 도시계획 조례", "국토계획법"]
            ], columns=["지자체", "조례명", "근거법률"])
            st.dataframe(df_ord, hide_index=True, use_container_width=True)
        with tabs[1]:
            st.write("✔️ 건축법 / 시행령 / 시행규칙 \n✔️ 국토의 계획 및 이용에 관한 법률 \n✔️ 건축물관리법")
        with tabs[2]:
            st.write("총 100여 개의 조례 및 상위법 위임 하위 법규(건설기술진흥법, 농지법, 주택법 등) 데이터를 교차 검증합니다.")
