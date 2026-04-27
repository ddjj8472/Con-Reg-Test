import streamlit as st
import requests
import json
import re
import time

def get_gemini_response(user_query, db_context=""):
    # [복구] 승욱 님 말씀대로 2.5 버전이 이 환경의 최신 모델입니다.
    MODEL_NAME = "gemini-2.5-flash" 
    
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        
        # [복구] v1 경로 사용 (2.5 버전은 v1에서 503 응답을 줬으므로 이 경로가 맞습니다)
        url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        
        prompt = f"""
        당신은 용인시 건축 조례 전문 해석 AI 플랫폼의 전문가입니다. 
        제공된 [참고 법규 데이터]를 최우선 근거로 사용하여 답변하십시오.

        [참고 법규 데이터]:
        {db_context if db_context else "직접적인 조례 데이터를 찾지 못했습니다. 일반적인 건축법령 지식에 기반하되 공식 확인이 필요함을 명시하십시오."}

        답변 규칙:
        1. 별표(*)와 슬래시(/)는 절대 사용하지 마십시오.
        2. 질문의 성격에 따라 형식을 달리하십시오.
        3. 6개 항목 구성 (사례 질문용): 결론, 적용 지역, 핵심 근거, 세부 해석, 원문 링크, 담당 기관.

        질문: {user_query}
        """
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        # [핵심] 503(High Demand) 오류를 해결하기 위한 자동 재시도 로직
        max_retries = 5 # 재시도 횟수를 늘림
        for i in range(max_retries):
            try:
                # 타임아웃 100초로 상향
                response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=100)
                
                if response.status_code == 200:
                    result = response.json()
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
                    text = text.replace("*", "").replace("/", "")
                    return text
                
                # 503(서버 부하) 발생 시 대기 시간을 늘려가며 재시도 (지수 백오프)
                if response.status_code == 503:
                    if i < max_retries - 1:
                        wait_time = (i + 1) * 3 # 3초, 6초, 9초... 순으로 대기
                        time.sleep(wait_time)
                        continue
                
                return f"엔진 응답 실패: {response.status_code} / {response.text}"
                
            except requests.exceptions.Timeout:
                if i < max_retries - 1:
                    time.sleep(3)
                    continue
                return "엔진 응답 시간 초과 (100초). 다시 시도해 주세요."

    except Exception as e:
        return f"통신 장애 발생: {str(e)}"
