import streamlit as st
import requests
import json
import re

def get_gemini_response(user_query):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        
        # 1. 2026년 기준 가장 안정적인 v1 경로와 1.5 Flash 모델을 사용합니다.
        # gemini-pro는 구형 명칭이라 404가 발생할 확률이 매우 높습니다.
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        
        # 지침: 별표, 슬래시, 영어 병기 금지 (사용자 요청 반영)
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"당신은 건축 조례 전문가입니다. 한국어로만 답변하세요. 별표나 슬래시 기호를 절대 사용하지 마세요. 질문: {user_query}"
                }]
            }]
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=15)
        result = response.json()
        
        if response.status_code == 200:
            text = result['candidates'][0]['content']['parts'][0]['text']
            # 특수 기호 강제 제거 필터
            text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
            text = text.replace("*", "").replace("/", "")
            return text
        else:
            # 404 발생 시 상세 메시지를 분석하여 다른 모델 추천
            error_msg = result.get('error', {}).get('message', '알 수 없는 오류')
            return f"서버 응답 오류({response.status_code}): {error_msg}\n(주의: API 키의 프로젝트 설정에서 Generative Language API가 활성화되어 있는지 확인하세요.)"

    except Exception as e:
        return f"통신 장애 발생: {str(e)}"
