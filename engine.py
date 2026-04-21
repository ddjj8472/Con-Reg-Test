import streamlit as st
import google.generativeai as genai
import re

def get_gemini_response(user_query):
    # 1. API 키 설정 (제공해주신 키를 직접 입력하거나 st.secrets 사용)
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except:
        api_key = "AIzaSyAbu0meqf6IgTe68_cAljCGdOK21ldxQMg"
    
    genai.configure(api_key=api_key)
    
    # 2. 모델 설정 (404 오류 방지를 위해 표준 명칭 사용)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 3. 응답 지침 설정
    system_instruction = """
    당신은 용인시 건축 조례 전문가입니다. 
    모든 답변은 반드시 다음 6개 항목에 맞춰 한국어로 작성하세요.
    별표나 슬래시 같은 특수 기호를 사용하지 마세요.
    답변 내용에 형태의 문구를 절대 포함하지 마세요.

    1. 결론
    2. 적용 지역
    3. 핵심 근거 조문
    4. 세부 설명
    5. 추가 확인 항목
    6. 담당 기관 및 후속 절차
    """
    
    full_prompt = f"{system_instruction}\n\n사용자 질문: {user_query}"
    
    try:
        response = model.generate_content(full_prompt)
        # 답변 텍스트 정제
        text = response.text
        clean_text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
        clean_text = clean_text.replace("*", "").replace("/", "")
        return clean_text
    except Exception as e:
        # 실제 오류 내용을 화면에 출력하여 디버깅 지원
        return f"인공지능 엔진 오류 발생: {str(e)}"
