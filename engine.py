# engine.py
import streamlit as st
import requests
import json
import re
import time

def get_semantic_keywords(user_query):
    """[Step 1] 시맨틱 키워드 도출"""
    MODEL_NAME = "gemini-2.5-flash"
    api_key = st.secrets["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    analysis_prompt = f"질문: '{user_query}' / 이 질문과 관련된 대한민국 법령 명칭과 핵심 전문 용어를 콤마(,)로 구분해서 5개만 나열해줘."
    payload = {"contents": [{"parts": [{"text": analysis_prompt}]}]}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        return response.json()['candidates'][0]['content']['parts'][0]['text'].strip() if response.status_code == 200 else ""
    except: return ""

def get_gemini_response(user_query, db_status, db_context, semantic_tags=""):
    """
    [Step 2] 최종 답변 생성:
    - 작성 규칙 4번을 범용적 지침으로 수정 (단편적 지시 배제)
    - 데이터 부족 시 일반 지식 강제 동원 로직 유지
    """
    MODEL_NAME = "gemini-2.5-flash" 
    api_key = st.secrets["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    if db_status in ["INCOMPLETE", "NO_DATA"]:
        status_instruction = """
        [매우 중요: 일반 지식 강제 동원 지침]
        현재 제공된 참조용 법규 데이터에 질문에 대한 직접적인 해답이 부족합니다.
        1. '### 세부 해석' 섹션의 첫 문장을 반드시 "현재 데이터베이스만으로는 정보 제공이 완료될 수 없어 일반 지식을 사용하여 답변합니다."로 시작하십시오.
        2. 위 문구를 쓴 직후부터는 데이터베이스에 내용이 없다는 사실을 반복하지 마십시오. 
        3. 당신이 보유한 대한민국 법령 및 행정 지식을 바탕으로 질문에 대한 실질적이고 구체적인 해답을 상세히 기술하십시오.
        """
    else:
        status_instruction = "제공된 데이터베이스 내용을 최우선 근거로 사용하여 전문적인 해석을 수행하십시오."

    prompt = f"""
    사용자의 질문에 대해 아래 3개 항목으로 구성된 전문 보고서를 작성하십시오.

    {status_instruction}

    [참조 데이터]: {db_context}
    [참조 키워드]: {semantic_tags}

    작성 규칙:
    1. 인삿말, 자기소개("전문가입니다" 등), 요약 표, 시스템 태그 노출을 모두 금지합니다.
    2. 항목은 반드시 ### 결론, ### 핵심 근거, ### 세부 해석 3가지만 사용하십시오.
    3. '### 핵심 근거'에는 DB에 조문이 없더라도 관련 상위 법령 명칭을 명시하십시오.
    4. '### 세부 해석'에서는 질문에 대한 실질적인 해답을 제공해야 합니다. "알 수 없다"거나 "한계가 있다"는 말을 반복하지 말고, 일반 지식을 활용해 기술하십시오.
    5. 별표(*)와 슬래시(/)를 사용하지 마십시오.

    질문: {user_query}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    for i in range(5):
        try:
            res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=100)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0]['text']
                # 정제 로직
                text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
                text = text.replace("*", "").replace("/", "")
                # 시스템 태그 제거
                for tag in ["[참조용 시맨틱 태그]", "[법률 분석 태그]", "[참조 데이터]", "[참조 키워드]"]:
                    text = text.replace(tag, "")
                return text.strip()
            time.sleep(2)
        except: continue
    return "AI 엔진 응답에 실패했습니다."
