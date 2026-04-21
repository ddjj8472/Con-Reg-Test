import streamlit as st
import requests
import json
import re

def get_gemini_response(user_query):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        # 가장 보수적이고 안정적인 경로와 모델(gemini-pro)을 사용합니다.
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"당신은 건축 조례 전문가입니다. 한국어로만 답변하세요. 별표나 슬래시를 절대 쓰지 마세요. 질문: {user_query}"
                }]
            }]
        }
        
        response = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload), timeout=15)
        result = response.json()
        
        if response.status_code == 200:
            text = result['candidates'][0]['content']['parts'][0]['text']
            # 별표, 슬래시, 인용구 강제 제거
            text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
            text = text.replace("*", "").replace("/", "")
            return text
        else:
            return f"오류 코드({response.status_code}): {result.get('error', {}).get('message')}"

    except Exception as e:
        return f"치명적 통신 오류: {str(e)}"
