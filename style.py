import streamlit as st

def apply_custom_style(is_dark: bool):
    c = {
        "bg": "#0e1117" if is_dark else "#ffffff",
        "side": "#262730" if is_dark else "#f4f6f9",
        "txt": "#fafafa" if is_dark else "#222222",
        "card": "#1e1e1e" if is_dark else "#ffffff",
        "border": "#333333" if is_dark else "#eaeaea",
        "msg_bg": "#1e3a8a" if is_dark else "#e1f5fe",
        "msg_txt": "#ffffff" if is_dark else "#000000",
        "tab": "#aaaaaa" if is_dark else "#555555",
        "btn_bg": "#333333" if is_dark else "#ffffff",
        "btn_bd": "#555555" if is_dark else "#cccccc"
    }

    st.markdown(f"""
    <style>
    /* 전체 메인 화면 및 폰트 동기화 */
    :is(.stApp, [data-testid="stHeader"]) {{ background-color: {c['bg']} !important; color: {c['txt']}; }}
    :is(html, body, [class*="css"], p, h1, h2, h3, h4, h5, h6, li) {{ font-size: 16px !important; color: {c['txt']} !important; }}
    
    /* 사이드바 다크모드 적용 */
    [data-testid="stSidebar"] {{ background-color: {c['side']} !important; }}
    [data-testid="stSidebar"] :is(p, span, h1, h2, h3, label, div[data-testid="stMarkdownContainer"]) {{ color: {c['txt']} !important; }}
    
    /* 일반 버튼 색상 */
    button[kind="secondary"] {{ background-color: {c['btn_bg']} !important; color: {c['txt']} !important; border: 1px solid {c['btn_bd']} !important; }}
    button[kind="secondary"]:hover {{ border-color: #1E88E5 !important; color: #1E88E5 !important; }}
    
    /* 상단 탭 디자인 */
    .stTabs [data-baseweb="tab-list"] {{ gap: 15px; border-bottom: 2px solid {c['border']}; }}
    .stTabs [data-baseweb="tab"] {{ height: 60px; font-size: 18px !important; font-weight: 600; color: {c['tab']}; }}
    .stTabs [aria-selected="true"] {{ color: #1E88E5 !important; }}
    
    /* 대화 상자 디자인 */
    .report-card {{ padding: 25px; border-radius: 12px; background-color: {c['card']}; border: 1px solid {c['border']}; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px; line-height: 1.6; }}
    .user-msg {{ background-color: {c['msg_bg']}; color: {c['msg_txt']}; padding: 15px; border-radius: 8px; border-left: 5px solid #0288d1; margin-bottom: 10px; font-weight: bold; }}
    
    /* 🔥 하단 채팅 입력창(st.chat_input) 다크모드 하얀 배경 겉도는 현상 철저히 제거 */
    [data-testid="stChatInput"] {{ background-color: {c['bg']} !important; }} /* 최외곽 여백 */
    [data-testid="stChatInput"] > div {{ background-color: transparent !important; }}
    /* 내부 텍스트 에어리어까지 색상 강제 주입 */
    [data-testid="stChatInput"] [data-baseweb="textarea"],
    [data-testid="stChatInput"] [data-baseweb="base-input"],
    [data-testid="stChatInput"] > div > div {{
        background-color: {c['card']} !important;
        border-color: {c['border']} !important;
    }}
    [data-testid="stChatInput"] textarea {{
        color: {c['txt']} !important;
        -webkit-text-fill-color: {c['txt']} !important;
        caret-color: {c['txt']} !important;
    }}
    [data-testid="stChatInput"] svg {{ fill: {c['txt']} !important; }} /* 전송 버튼(종이비행기) 색상 */
    </style>
    """, unsafe_allow_html=True)
