import streamlit as st
import requests
import json
import re
import time

def get_gemini_response(user_query, db_context=""):
    # 1.5-flash는 현재 가장 빠르고 안정적인 모델입니다.
    MODEL_NAME = "gemini-1.5-flash" 
    
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        
        # [핵심 수정] v1 -> v1beta로 변경
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        
        prompt = f"""
        당신은 용인시 건축 조례 및 법령 전문가입니다. 
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
        
        # 재시도 로직 포함
        max_retries = 3
        for i in range(max_retries):
            try:
                response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=100)
                
                if response.status_code == 200:
                    result = response.json()
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
                    text = text.replace("*", "").replace("/", "")
                    return text
                
                # 404 에러가 계속되면 모델명을 확인해야 함
                if response.status_code == 404:
                    return f"모델을 찾을 수 없습니다(404). URL 또는 모델명을 확인하세요: {MODEL_NAME}"
                
                # 503 에러 발생 시 재시도
                if response.status_code == 503 and i < max_retries - 1:
                    time.sleep(2)
                    continue
                
                return f"엔진 응답 실패: {response.status_code} / {response.text}"
                
            except requests.exceptions.Timeout:
                if i < max_retries - 1:
                    time.sleep(2)
                    continue
                return "엔진 응답 시간 초과 (100초)."

    except Exception as e:
        return f"통신 장애 발생: {str(e)}"
