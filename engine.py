import streamlit as st
import requests
import json
import re

def get_gemini_response(user_query):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        
        # 1. 사용 가능한 모델 리스트를 먼저 가져옵니다.
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        list_response = requests.get(list_url, timeout=10)
        
        if list_response.status_code != 200:
            return f"모델 목록 호출 실패({list_response.status_code}): {list_response.text}"
        
        models_data = list_response.json().get('models', [])
        
        # 2. 리스트에서 사용할 수 있는 모델 하나를 찾습니다. (flash 우선, 그 다음 pro)
        target_model = ""
        available_names = [m['name'] for m in models_data]
        
        for name in available_names:
            if "gemini-1.5-flash" in name:
                target_model = name
                break
        
        if not target_model:
            for name in available_names:
                if "gemini-pro" in name or "gemini-1.0-pro" in name:
                    target_model = name
                    break
        
        if not target_model:
            return f"사용 가능한 Gemini 모델을 찾을 수 없습니다. (검색된 리스트: {', '.join(available_names[:3])}...)"

        # 3. 찾은 모델의 정확한 이름으로 답변을 요청합니다.
        # target_model은 이미 'models/gemini-1.5-flash' 형태입니다.
        gen_url = f"https://generativelanguage.googleapis.com/v1beta/{target_model}:generateContent?key={api_key}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"당신은 용인시 건축 조례 전문가입니다. 한국어로만 답변하세요. 별표나 슬래시를 절대 쓰지 마세요.\n\n질문: {user_query}"
                }]
            }]
        }
        
        gen_response = requests.post(gen_url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload), timeout=15)
        
        if gen_response.status_code == 200:
            result = gen_response.json()
            text = result['candidates'][0]['content']['parts'][0]['text']
            # 특수기호 및 인용구 제거
            text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
            text = text.replace("*", "").replace("/", "")
            return f"[사용 모델: {target_model}]\n\n{text}"
        else:
            return f"답변 생성 실패({gen_response.status_code}): {gen_response.text}"

    except Exception as e:
        return f"통신 장애 발생: {str(e)}"
