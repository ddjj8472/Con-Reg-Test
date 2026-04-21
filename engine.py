import streamlit as st
import requests
import json
import re

def get_gemini_response(user_query):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        # API 주소를 v1으로 고정하여 v1beta 오류를 원천 차단합니다.
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        
        # 지침을 프롬프트 본문에 합칩니다. (별표, 슬래시, 영어 금지)
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"""당신은 용인시 건축 조례 전문가입니다. 한국어로만 답변하세요. 
                    규칙:
                    1. 답변에 영어 번역을 절대 병기하지 마세요.
                    2. 별표나 슬래시 기호를 절대 사용하지 마세요.
                    3. [cite] 등 모든 인용 표시를 제거하세요.
                    4. 단순 개념은 설명문으로, 사례는 아래 6개 항목으로 답하세요.
                    (1. 결론 2. 적용 지역 3. 핵심 근거 조문 4. 세부 설명 5. 추가 확인 항목 6. 담당 기관 및 후속 절차)
                    
                    질문: {user_query}"""
                }]
            }]
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        result = response.json()
        
        if response.status_code == 200:
            text = result['candidates'][0]['content']['parts'][0]['text']
            # 마지막 필터링
            text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
            text = text.replace("*", "").replace("/", "")
            return text
        else:
            return f"서버 응답 오류({response.status_code}): {result['error']['message']}"

    except Exception as e:
        return f"통신 오류 발생: {str(e)}"
