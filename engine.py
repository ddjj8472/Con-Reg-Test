import streamlit as st
from google import genai
import re

def get_gemini_response(user_query):
    try:
        # 스트림릿 Secrets에서 키 호출
        api_key = st.secrets["GEMINI_API_KEY"]
        
        # 최신 SDK 클라이언트 생성
        client = genai.Client(api_key=api_key)
        
        # 질문과 지침을 하나로 합침 (영어 금지 및 특수기호 금지 강제)
        combined_prompt = f"""
        당신은 용인시 건축 조례 전문가입니다. 다음 규칙을 엄격히 지켜 한국어로만 답변하세요.

        1. 절대 답변에 영어 번역을 병기하지 마세요.
        2. 답변 전체에서 별표나 슬래시 기호를 절대 사용하지 마세요.
        3. [cite] 문구는 모두 삭제하세요.
        4. 단순 개념은 일반 설명문으로, 사례 해석은 아래 6개 번호 항목으로 작성하세요.
           1. 결론
           2. 적용 지역
           3. 핵심 근거 조문
           4. 세부 설명
           5. 추가 확인 항목
           6. 담당 기관 및 후속 절차

        사용자 질문: {user_query}
        """
        
        # 최신 방식의 콘텐츠 생성
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=combined_prompt
        )
        
        if response and response.text:
            # 기호 강제 제거 필터
            clean_text = re.sub(r"\[?cite:\s?\d+\]?", "", response.text)
            clean_text = clean_text.replace("*", "").replace("/", "")
            return clean_text
        else:
            return "AI가 답변을 생성하지 못했습니다."

    except Exception as e:
        return f"엔진 가동 오류 발생: {str(e)}"
