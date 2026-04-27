# style.py
import streamlit as st

def apply_custom_style(is_dark: bool):
    # 1. 삼항 연산자를 활용한 색상 변수 딕셔너리화 (코드 길이 대폭 축소)
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

    # 2. CSS :is() 선택자를 활용한 중복 구문 압축
    st.markdown(f"""
    <style>
    /* 메인 화면 & 헤더 동기화 */
    :is(.stApp, [data-testid="stHeader"]) {{ background-color: {c['bg']} !important; color: {c['txt']}; }}
    
    /* 기본 텍스트 폰트 및 색상 강제 적용 */
    :is(html, body, [class*="css"], p, h1, h2, h3, h4, h5, h6, li) {{ font-size: 16px !important; color: {c['txt']} !important; }}
    
    /* 사이드바 배경 및 내부 텍스트 */
    [data-testid="stSidebar"] {{ background-color: {c['side']} !important; }}
    [data-testid="stSidebar"] :is(p, span, h1, h2, h3, label, div[data-testid="stMarkdownContainer"]) {{ color: {c['txt']} !important; }}
    
    /* 일반 버튼 (Secondary) */
    button[kind="secondary"] {{ background-color: {c['btn_bg']} !important; color: {c['txt']} !important; border: 1px solid {c['btn_bd']} !important; }}
    button[kind="secondary"]:hover {{ border-color: #1E88E5 !important; color: #1E88E5 !important; }}
    
    /* 상단 탭 */
    .stTabs [data-baseweb="tab-list"] {{ gap: 15px; border-bottom: 2px solid {c['border']}; }}
    .stTabs [data-baseweb="tab"] {{ height: 60px; font-size: 18px !important; font-weight: 600; color: {c['tab']}; }}
    .stTabs [aria-selected="true"] {{ color: #1E88E5 !important; }}
    
    /* 채팅 박스 및 보고서 카드 (줄바꿈 최소화) */
    .report-card {{ padding: 30px; border-radius: 12px; background-color: {c['card']}; border: 1px solid {c['border']}; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin: 10px 0 20px; }}
    .user-msg {{ background-color: {c['msg_bg']}; color: {c['msg_txt']}; padding: 15px; border-radius: 8px; border-left: 5px solid #0288d1; margin-bottom: 10px; font-weight: bold; }}

    /* 채팅 입력창 하단 고정 및 하단 영역 배경 처리 */
    .stApp::after {{ content: ""; position: fixed; left: 22rem; right: 0; bottom: 0; height: 95px; background-color: {c['bg']}; z-index: 998; pointer-events: none; }}
    [data-testid="stChatInput"] {{ position: fixed !important; bottom: 35px !important; left: 22rem !important; right: 2rem !important; z-index: 9999 !important; }}
    .main .block-container {{ padding-bottom: 240px !important; }}
     
    </style>
    """, unsafe_allow_html=True)
