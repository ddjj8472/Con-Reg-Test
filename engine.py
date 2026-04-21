import streamlit as st
import google.generativeai as genai
import re

def get_gemini_response(user_query):
    # API 키 직접 기입 방식
    genai.configure(api_key="AIzaSyAbu0meqf6IgTe68_cAljCGdOK21ldxQMg")
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    system_instruction = """
    당신은 용인시 건축 조례 전문가입니다. 
    모든 답변은 반드시 다음 6개 항목에 맞춰 한국어로 작성하세요.
    항목 구분 시 별표나 슬래시 같은 특수 기호를 사용하지 마세요.
    답변 내용에 형태의 인용 문구를 절대 포함하지 마세요.

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
        text = response.text
        # 인용구 및 특수 기호 강제 제거
        clean_text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
        clean_text = clean_text.replace("*", "").replace("/", "")
        return clean_text
    except Exception as e:
        return "분석 엔진 가동 중 오류가 발생했습니다."
