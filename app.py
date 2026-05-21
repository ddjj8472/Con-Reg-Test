import streamlit as st
import pandas as pd
import html
import io
from docx import Document

st.set_page_config(
    page_title="용인시 건축 조례 지원 플랫폼",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

from widget_utils import inject_floating_button
from processor import handle_ai_analysis, generate_civil_document
from style import apply_custom_style
from components import render_user_message, render_ai_report
from storage import load_history, save_history

inject_floating_button()

if "user_id" not in st.session_state:
    st.session_state.user_id = "guest"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_history(st.session_state.user_id)
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "dark_mode_toggle" not in st.session_state:
    st.session_state.dark_mode_toggle = st.session_state.dark_mode
if "selected_index" not in st.session_state:
    st.session_state.selected_index = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "main"
if "qna_list" not in st.session_state:
    st.session_state.qna_list = []


def sync_dark_mode():
    st.session_state.dark_mode = st.session_state.dark_mode_toggle


def persist_history():
    save_history(st.session_state.chat_history, st.session_state.user_id)


apply_custom_style(st.session_state.dark_mode)

st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
html, body, .stApp, p, h1, h2, h3, h4, h5, h6, label, input, textarea, div, button {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
}
div[data-testid="stButton"] button, div[data-testid="stFormSubmitButton"] button,
div[data-testid="stPopover"] button {
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.chat-row-shell {
    margin: 0 0 -2px 0;
    padding: 0;
}
.chat-row-note {
    font-size: 11px;
    color: #777;
    margin: -8px 0 6px 8px;
}
/* 대화 이력 줄 안의 버튼들이 하나의 카드처럼 보이도록 보정 */
div[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"]:has(button[kind="secondary"]) {
    gap: 0.35rem;
    align-items: center;
    margin-bottom: 0.25rem;
}
div[data-testid="stSidebar"] div[data-testid="stPopover"] button {
    min-height: 38px !important;
    padding: 0.25rem 0.4rem !important;
    font-size: 18px !important;
}
</style>
""", unsafe_allow_html=True)


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
        text = chat.get("title", "") + " "
        for msg in chat.get("messages", []):
            text += msg.get("query", "") + " " + msg.get("response", "") + " "
        if not query or query in text.lower():
            results.append((idx, chat))
    st.caption(f"검색 결과 {len(results)}개" if query else "최근 대화")
    if not results:
        st.warning("검색 결과가 없습니다.")
        return
    with st.container(height=400, border=False):
        for idx, chat in reversed(results[-20:]):
            title = chat.get("title", "새 대화")
            time_str = chat.get("updated_at", chat.get("created_at", ""))
            if st.button(f"💬 {title[:25]}...\n\n{time_str}", key=f"dialog_chat_{idx}", use_container_width=True):
                st.session_state.selected_index = idx
                st.session_state.current_page = "main"
                st.rerun()
            st.markdown("---")


with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1048/1048978.png", width=50)
    st.title("플랫폼 제어")

    with st.expander("👤 실무자 시스템 인증", expanded=(st.session_state.user_id == "guest")):
        if st.session_state.user_id == "guest":
            tabs = st.tabs(["로그인", "회원가입"])
            with tabs[0]:
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
            with tabs[1]:
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
    st.subheader("📌 메인 메뉴")
    if st.button("🏠 메인화면 (AI 챗봇)", use_container_width=True):
        st.session_state.current_page = "main"; st.rerun()
    if st.button("📝 민원 양식 자동생성", use_container_width=True):
        st.session_state.current_page = "doc_gen"; st.rerun()
    if st.button("💡 FAQ & Q&A 게시판", use_container_width=True):
        st.session_state.current_page = "qna"; st.rerun()
    if st.button("🗺️ 플랫폼 사이트맵", use_container_width=True):
        st.session_state.current_page = "sitemap"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    st.toggle("🌙 다크 모드", key="dark_mode_toggle", on_change=sync_dark_mode)
    st.markdown("---")

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
    with st.container(height=250, border=True):
        if st.session_state.chat_history:
            items = list(enumerate(st.session_state.chat_history))
            items.sort(
                key=lambda item: (
                    item[1].get("pinned", False),
                    item[1].get("updated_at", item[1].get("created_at", ""))
                ),
                reverse=True
            )

            for actual_index, chat in items:
                time_str = chat.get("updated_at", chat.get("created_at", "00-00 00:00"))[5:16]
                title = chat.get("title", "새 대화")
                short_title = title[:13] + ".." if len(title) > 13 else title
                pin_mark = "📌 " if chat.get("pinned", False) else ""
                pin_label = "고정 해제" if chat.get("pinned", False) else "상단 고정"

                st.markdown('<div class="chat-row-shell">', unsafe_allow_html=True)
                row_col, menu_col = st.columns([0.84, 0.16], gap="small")

                with row_col:
                    if st.button(
                        f"{pin_mark}🕒 {time_str} | {short_title}",
                        key=f"hist_{actual_index}",
                        use_container_width=True
                    ):
                        st.session_state.selected_index = actual_index
                        st.session_state.current_page = "main"
                        st.rerun()

                with menu_col:
                    with st.popover("⋯", use_container_width=True):
                        st.caption("대화 옵션")

                        new_title = st.text_input(
                            "제목 수정",
                            value=title,
                            key=f"rename_input_{actual_index}"
                        )

                        if st.button("제목 저장", key=f"rename_save_{actual_index}", use_container_width=True):
                            clean_title = new_title.strip() or "새 대화"
                            st.session_state.chat_history[actual_index]["title"] = clean_title
                            persist_history()
                            st.toast("제목이 수정되었습니다.", icon="✏️")
                            st.rerun()

                        if st.button(pin_label, key=f"pin_toggle_{actual_index}", use_container_width=True):
                            st.session_state.chat_history[actual_index]["pinned"] = not chat.get("pinned", False)
                            persist_history()
                            st.rerun()

                        st.divider()
                        confirm_delete = st.checkbox("삭제 확인", key=f"confirm_delete_{actual_index}")
                        if st.button("삭제", key=f"delete_one_{actual_index}", type="primary", use_container_width=True):
                            if confirm_delete:
                                st.session_state.chat_history.pop(actual_index)
                                if st.session_state.selected_index == actual_index:
                                    st.session_state.selected_index = None
                                elif st.session_state.selected_index is not None and st.session_state.selected_index > actual_index:
                                    st.session_state.selected_index -= 1
                                persist_history()
                                st.toast("대화가 삭제되었습니다.", icon="🗑️")
                                st.rerun()
                            else:
                                st.warning("삭제하려면 먼저 삭제 확인을 체크하세요.")
                st.markdown('</div>', unsafe_allow_html=True)
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


if st.session_state.current_page == "main":
    st.title("🏢 건축 조례 및 법령 해석 AI")
    st.markdown("<p style='color: #666; font-size: 1.1em;'>건축사, 시공사, 인허가 담당자의 신속한 의사결정을 돕는 심층 규제 분석 엔진입니다.</p>", unsafe_allow_html=True)
    chat_box = st.container(height=500, border=False)
    user_query = st.chat_input("예: 용인시 처인구 자연녹지지역의 건폐율과 용적률 기준은?")

    with chat_box:
        if st.session_state.selected_index is not None and 0 <= st.session_state.selected_index < len(st.session_state.chat_history):
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
            st.image("https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop", use_container_width=True)
            st.markdown("""
            <div style="text-align:center; padding: 30px; background: rgba(128,128,128,0.05); border-radius: 12px; margin-top: 15px;">
                <h3 style="color: #0b459c; margin-bottom: 8px;">어떤 규제를 검토해 드릴까요?</h3>
                <p style="color: #555; font-size: 14px; line-height: 1.6;">경기도/용인시 조례 및 상위 법령 데이터베이스를 기반으로 분석합니다.</p>
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

elif st.session_state.current_page == "doc_gen":
    st.title("📝 맞춤형 건축 민원 양식 자동완성")
    st.info("복잡한 민원 내용을 입력하면 AI가 용인시 행정 양식에 맞춰 문서를 작성합니다. 법령 검토는 챗봇을 이용해 주세요.")
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
    department_map = {"건축허가 관련": "건축허가과", "건축선 문의": "건축과", "일조권 민원": "건축과", "불법건축물 신고": "건축과", "용도변경 문의": "건축허가과", "주차장 기준 문의": "교통정책과", "건축물 해석 문의": "건축과", "기타": "민원여권과"}
    col1, col2 = st.columns(2)
    with col1:
        civil_type = st.selectbox("📌 민원 유형 선택", list(required_docs.keys()))
    with col2:
        site_address = st.text_input("📍 대상 건축물 주소", placeholder="예: 경기도 용인시 처인구 중부대로 1199")
    civil_content = st.text_area("✏️ 민원 상세 내용", height=150)
    if st.button("✨ AI 민원 양식 생성하기", use_container_width=True, type="primary"):
        if not site_address or not civil_content:
            st.error("주소와 민원 내용을 모두 입력해주세요.")
        else:
            result = generate_civil_document(civil_type, site_address, civil_content)
            st.subheader("📄 생성된 민원서")
            st.markdown(f"<div style='padding:20px; border:1px solid #ddd; border-radius:8px; background:rgba(0,0,0,0.02);'>{result}</div>", unsafe_allow_html=True)
            tabs = st.tabs(["📎 필요 서류", "🏢 담당 부서", "📥 파일 다운로드"])
            with tabs[0]:
                for doc_name in required_docs.get(civil_type, required_docs["기타"]):
                    st.write(f"✔️ {doc_name}")
            with tabs[1]:
                st.info(f"📌 용인시청 또는 관할 구청 **{department_map.get(civil_type, '민원여권과')}** 문의 요망")
            with tabs[2]:
                doc = Document()
                doc.add_heading('용인시 건축 행정 민원서', level=1)
                doc.add_paragraph(f"민원 유형: {civil_type}\n대상 주소: {site_address}")
                doc.add_heading('민원 내용', level=2)
                doc.add_paragraph(result)
                buffer = io.BytesIO()
                doc.save(buffer)
                buffer.seek(0)
                st.download_button("💾 DOCX 양식 다운로드", buffer, "용인시_건축민원서.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

elif st.session_state.current_page == "qna":
    st.title("💡 커뮤니티 Q&A")
    st.write("플랫폼 사용법이나 애매한 규제 해석에 대해 질문을 남겨주세요.")
    q_title = st.text_input("제목")
    q_content = st.text_area("내용")
    if st.button("질문 등록", use_container_width=True):
        if q_title and q_content:
            st.session_state.qna_list.append({"title": q_title, "content": q_content, "status": "대기중", "answer": ""})
            st.rerun()
    for q in st.session_state.qna_list:
        with st.expander(f"[{q['status']}] {q['title']}"):
            st.markdown(f"**Q.** {q['content']}")

elif st.session_state.current_page == "sitemap":
    st.title("🗺️ 시스템 아키텍처 및 취급 데이터")
    st.write("본 플랫폼은 AI 엔진과 법규 DB를 연동하여 동작합니다.")
    df_ord = pd.DataFrame([
        ["경기도", "경기도 건축 조례", "건축법"],
        ["경기도", "경기도 건축기본조례", "건축기본법"],
        ["용인시", "용인시 건축 조례", "건축법"],
        ["용인시", "용인시 도시계획 조례", "국토계획법"]
    ], columns=["지자체", "조례명", "근거법률"])
    st.dataframe(df_ord, hide_index=True, use_container_width=True)
