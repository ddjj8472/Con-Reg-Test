import streamlit as st

def apply_custom_style(dark_mode):
    if dark_mode:
        bg_main, bg_sidebar, text_main = "#0e1117", "#262730", "#fafafa"
        card_bg, card_border, user_msg_bg, user_msg_text = "#1e1e1e", "#333333", "#1e3a8a", "#ffffff"
        tab_color, btn_bg, btn_border = "#aaaaaa", "#333333", "#555555"
    else:
        bg_main, bg_sidebar, text_main = "#ffffff", "#f4f6f9", "#222222"
        card_bg, card_border, user_msg_bg, user_msg_text = "#ffffff", "#eaeaea", "#e1f5fe", "#000000"
        tab_color, btn_bg, btn_border = "#555555", "#ffffff", "#cccccc"

    st.markdown(f"""
        <style>
        .stApp {{ background-color: {bg_main}; color: {text_main}; }}
        [data-testid="stHeader"] {{ background-color: {bg_main} !important; }}
        [data-testid="stSidebar"] {{ background-color: {bg_sidebar} !important; }}
        .report-card {{ padding: 30px; border-radius: 12px; background-color: {card_bg}; border: 1px solid {card_border}; color: {text_main}; }}
        .user-msg {{ background-color: {user_msg_bg}; color: {user_msg_text}; padding: 15px; border-radius: 8px; margin-bottom: 10px; }}
        /* 추가적인 모든 CSS 코드를 여기에 넣으세요 */
        </style>
        """, unsafe_allow_html=True)
