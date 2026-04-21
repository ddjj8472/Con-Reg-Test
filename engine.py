import streamlit as st
import google.generativeai as genai
import re

def get_gemini_response(user_query):
    try:
        # 보안 비밀에서 키 불러오기
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        
        # 404 오류 해결을 위한 핵심 로직: 
        # 시스템이 모델을 찾지 못할 경우를 대비해 두 가지 명칭을 차례로 시도합니다.
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
        except:
            model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        system_instruction = """
        당신은 용인시 건축 조례 및 법령 전문가입니다. 
        사용자의 질문 성격에 따라 다음 두 가지 방식 중 하나를 선택하여 답변하세요.

        1. 단순 개념 질문 (예: 건폐율의 정의)
           해당 개념의 정의와 산식, 건축적 의미를 일반적인 설명문 형태로 작성하세요.
           번호를 매기거나 6가지 항목으로 나누지 마세요.

        2. 구체적 사례 및 법적 해석 질문 (예: 용인시 건폐율 기준)
           반드시 다음 6가지 항목을 엄격히 준수하여 보고서 형태로 작성하세요.
           1. 결론
           2. 적용 지역
           3. 핵심 근거 조문
           4. 세부 설명
           5. 추가 확인 항목
           6. 담당 기관 및 후속 절차

        공통 금지 사항:
        별표나 슬래시 같은 특수 기호를 절대 사용하지 마세요.
        인용 표시나 cite 문구를 절대 포함하지 마세요.
        """
        
        full_prompt = f"{system_instruction}\n\n사용자 질문: {user_query}"
        
        response = model.generate_content(full_prompt)
        text = response.text
        
        # 불필요한 기호 및 인용구 강제 제거 필터
        clean_text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
        clean_text = clean_text.replace("*", "").replace("/", "")
        
        return clean_text
        
    except Exception as e:
        # 실제 오류 내용을 아주 상세히 보여주도록 수정했습니다.
        return f"현재 시스템 환경 문제로 분석이 지연되고 있습니다. 오류 상세: {str(e)}"
