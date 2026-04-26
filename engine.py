import streamlit as st
import requests
import json
import re

def get_gemini_response(user_query, db_context=""):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        
        # DB 내용을 참고하여 답변하도록 프롬프트 강화
        prompt = f"""
        당신은 용인시 건축 조례 및 법령 전문가입니다. 
        제공된 [참고 법규 데이터]를 최우선 근거로 사용하여 답변하십시오.

        [참고 법규 데이터]:
        {db_context if db_context else "직접적인 조례 데이터를 찾지 못했습니다. 일반적인 건축법령 지식에 기반하되 공식 확인이 필요함을 명시하십시오."}

        규칙:
        1. 별표(*)와 슬래시(/)는 절대 사용하지 마십시오.
        2. 조례와 상위 법령(차용법규)의 관계가 있다면 이를 명확히 설명하십시오.
        3. 반드시 다음 6개 항목으로 보고서를 작성하십시오.
           1. 결론
           2. 적용 지역 및 법적 위계
           3. 핵심 근거 조문 (DB에 있는 경우 조문 번호 명시)
           4. 세부 해석 및 설명
           5. 추가 확인 사항 및 원문 링크 (제공된 link 활용)
           6. 담당 기관 및 후속 절차

        질문: {user_query}
        """
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        # 대기 시간을 60초로 늘려 타임아웃 방지
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        
        if response.status_code == 200:
            text = response.json()['candidates'][0]['content']['parts'][0]['text']
            # 정제 필터
            text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
            return text.replace("*", "").replace("/", "")
        else:
            return "엔진 응답에 실패했습니다."
    except Exception as e:
        return f"통신 장애: {str(e)}"
