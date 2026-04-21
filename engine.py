import streamlit as st
import google.generativeai as genai
import re

def get_gemini_response(user_query):
    # 스트림릿 Secrets에서 API 키를 안전하게 불러옵니다.
    # 깃허브에는 키가 올라가지 않으므로 보안이 유지됩니다.
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        return "오류: 스트림릿 Secrets에 GEMINI_API_KEY가 설정되지 않았습니다."

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 질문 성격에 따른 답변 형식 지침
    system_instruction = """
    당신은 용인시 건축 조례 및 법령 전문가입니다. 
    사용자의 질문 성격에 따라 다음 두 가지 방식 중 하나를 선택하여 답변하세요.

    1. 단순 개념 질문 (예: 건폐율의 정의, 용적률이란?)
       - 해당 개념의 정의와 산식, 건축적 의미를 일반적인 설명문 형태로 작성하세요.
       - 6가지 항목으로 나누지 마세요.

    2. 구체적 사례 및 법적 해석 질문 (예: 용인시 건폐율 기준, 특정 대지의 건축 가능 여부)
       - 반드시 다음 6가지 항목을 엄격히 준수하여 보고서 형태로 작성하세요.
         1. 결론
         2. 적용 지역
         3. 핵심 근거 조문
         4. 세부 설명
         5. 추가 확인 항목
         6. 담당 기관 및 후속 절차

    공통 금지 사항:
    - 답변 내에 별표나 슬래시 같은 특수 기호를 절대 사용하지 마세요.
    -와 같은 인용 표시는 절대 포함하지 마세요.
    - 모든 답변은 한국어로 작성하세요.
    """
    
    full_prompt = f"{system_instruction}\n\n사용자 질문: {user_query}"
    
    try:
        response = model.generate_content(full_prompt)
        text = response.text
        
        # 잔여 인용구 및 특수 기호(별표, 슬래시) 강제 제거 필터
        clean_text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
        clean_text = clean_text.replace("*", "").replace("/", "")
        
        return clean_text
    except Exception as e:
        return f"분석 엔진 가동 중 오류가 발생했습니다: {str(e)}"
