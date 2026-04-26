import streamlit as st
import requests
import json
import re

def get_gemini_response(user_query):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        
        # 확인된 리스트 중 가장 성능이 좋은 2.5 Flash 모델 경로를 사용합니다.
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        
        # 지침: 영어 병기 금지, 별표 및 슬래시 사용 금지
        prompt = f"""
        당신은 용인시 건축 조례 전문가입니다. 다음 규칙을 엄격히 지켜 한국어로만 답변하세요.

        1. 답변에 영어 번역을 절대 넣지 마세요. (예: 결론 (Conclusion) 금지)
        2. 답변 전체에서 별표(*)나 슬래시(/) 기호를 절대 사용하지 마세요.
        3. [cite] 등 모든 인용구 표시를 삭제하세요.
        4. 단순 개념 질문은 일반 설명문으로 작성하세요.
        5. 사례 해석 질문은 반드시 아래 6개 항목으로 나누어 작성하세요.
           1. 결론
           2. 적용 지역
           3. 핵심 근거 조문
           4. 세부 설명
           5. 추가 확인 항목
           6. 담당 기관 및 후속 절차

        질문: {user_query}
        """
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=100)
        result = response.json()
        
        if response.status_code == 200:
            text = result['candidates'][0]['content']['parts'][0]['text']
            # 마지막 필터링: 별표와 슬래시 강제 제거
            text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
            text = text.replace("*", "").replace("/", "")
            return text
        else:
            error_msg = result.get('error', {}).get('message', '알 수 없는 오류')
            return f"엔진 실행 오류: {error_msg}"

    except Exception as e:
        return f"통신 장애 발생: {str(e)}"
