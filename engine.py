import streamlit as st
import requests
import json
import re

def get_gemini_response(user_query):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        
        # v1beta 대신 정식 버전인 v1 경로를 사용합니다.
        # 이 경로는 안정화된 gemini-1.5-flash 모델을 가장 잘 찾습니다.
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        
        # 질문과 지침을 하나로 합침 (특수 기호 및 영어 절대 금지)
        prompt = f"""
        당신은 용인시 건축 조례 전문가입니다. 다음 규칙을 엄격히 지켜 한국어로만 답변하세요.

        1. 절대 답변에 영어 번역을 병기하지 마세요. (예: 결론 (Conclusion) 금지)
        2. 답변 전체에서 별표나 슬래시 기호를 절대 사용하지 마세요.
        3. [cite] 등 인용구 표시를 모두 삭제하세요.
        4. 단순 개념은 일반 설명문으로, 사례 해석은 아래 6개 항목으로 답하세요.
           1. 결론
           2. 적용 지역
           3. 핵심 근거 조문
           4. 세부 설명
           5. 추가 확인 항목
           6. 담당 기관 및 후속 절차

        사용자 질문: {user_query}
        """
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=15)
        result = response.json()
        
        if response.status_code == 200:
            text = result['candidates'][0]['content']['parts'][0]['text']
            # 마지막 필터링 (별표, 슬래시 강제 제거)
            text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
            text = text.replace("*", "").replace("/", "")
            return text
        else:
            # 오류 발생 시 상세 내용을 출력하여 바로 잡을 수 있게 합니다.
            error_msg = result.get('error', {}).get('message', '상세 불명 오류')
            return f"서버 연결 오류: {error_msg}"

    except Exception as e:
        return f"통신 장애 발생: {str(e)}"
