import streamlit as st
import requests
import json
import re

def get_gemini_response(user_query):
    try:
        # 깃허브가 아닌 스트림릿 Secrets에서 키를 가져오므로 보안이 유지됩니다.
        api_key = st.secrets["GEMINI_API_KEY"]
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"당신은 용인시 건축 조례 전문가입니다. 한국어로만 답변하고 별표나 슬래시를 쓰지 마세요.\n\n질문: {user_query}"
                }]
            }]
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        result = response.json()
        
        if response.status_code == 200:
            text = result['candidates'][0]['content']['parts'][0]['text']
            # 특수기호 및 인용구 제거
            text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
            text = text.replace("*", "").replace("/", "")
            return text
        else:
            # 여기서 유출 메시지가 뜨면 키가 또 노출된 겁니다.
            return f"오류 발생: {result.get('error', {}).get('message')}"
            
    except Exception as e:
        return f"통신 오류: {str(e)}"
