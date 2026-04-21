import streamlit as st
import requests
import json

def get_gemini_response(user_query):
    api_key = st.secrets["GEMINI_API_KEY"]
    
    # 서버에 현재 사용 가능한 모델 목록을 요청합니다.
    url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
    
    try:
        response = requests.get(url, timeout=10)
        result = response.json()
        
        if response.status_code == 200:
            # 사용 가능한 모델 이름들을 하나로 합쳐서 반환합니다.
            models = [m['name'] for m in result.get('models', [])]
            if not models:
                return "접근 가능한 모델이 하나도 없습니다. API 키 설정을 확인하세요."
            return "사용 가능 모델 리스트: " + ", ".join(models)
        else:
            return f"모델 리스트 호출 실패: {result.get('error', {}).get('message', 'Unknown Error')}"
            
    except Exception as e:
        return f"진단 중 통신 오류: {str(e)}"
