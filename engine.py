# engine.py
import streamlit as st
import requests
import json
import re
import time

def get_semantic_keywords(user_query):
    """[Step 1] 내부 검색 전략 수립을 위한 시맨틱 추출"""
    MODEL_NAME = "gemini-2.5-flash"
    api_key = st.secrets["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    analysis_prompt = f"질문: '{user_query}' / 이 질문과 관련된 법령 명칭과 전문 용어를 콤마(,)로 구분해서 5개만 나열해줘."
    payload = {"contents": [{"parts": [{"text": analysis_prompt}]}]}
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        return response.json()['candidates'][0]['content']['parts'][0]['text'].strip() if response.status_code == 200 else ""
    except: return ""

def get_gemini_response(user_query, db_status, db_context, semantic_tags=""):
    """
    [Step 2] 최종 답변 생성:
    - 시스템 분류 라벨([위임법령 핵심] 등) 노출 전면 차단
    - 민원인 중심의 정갈한 법률 보고서 형식 유지
    """
    MODEL_NAME = "gemini-2.5-flash" 
    api_key = st.secrets["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    if db_status in ["INCOMPLETE", "NO_DATA"]:
        status_instruction = """
        [데이터 보완 지침]
        제공된 데이터베이스에 직접적인 정보가 부족한 상태입니다.
        1. '### 세부 해석' 섹션의 첫 문장을 반드시 "현재 데이터베이스만으로는 정보 제공이 완료될 수 없어 일반 지식을 사용하여 답변합니다."로 시작하십시오.
        2. 위 폴백(Fallback) 문구 고지 후에는 당신의 지식을 바탕으로 질문에 대한 명확한 해답을 상세히 기술하십시오.
        """
    else:
        status_instruction = "제공된 데이터베이스 내용을 최우선 근거로 사용하여 답변하십시오."

    prompt = f"""
    민원인의 질문에 대해 아래 3개 항목으로 구성된 보고서를 작성하십시오.

    {status_instruction}

    [참조용 데이터베이스]: {db_context}
    [참조용 키워드]: {semantic_tags}

    작성 및 금지 규칙 (위반 시 시스템 오류 발생):
    1. 도입부 인사말이나 자기소개를 절대 하지 마십시오. 바로 ### 결론 항목으로 시작합니다.
    2. 다음 3개 항목만 사용하십시오: ### 결론, ### 핵심 근거, ### 세부 해석.
    3. **절대 금지**: [위임법령 핵심], [조례 핵심], [참조용 데이터베이스] 등 대괄호로 둘러싸인 시스템 분류 명칭을 본문에 절대 노출하지 마십시오.
    4. ### 핵심 근거 작성 시 법령의 명칭(예: 건축물관리법)만 나열하십시오.
    5. '### 세부 해석'에서는 일반 지식을 활용해 실질적인 정보와 해답을 상세히 기술하십시오.
    6. 별표(*)와 슬래시(/) 사용을 절대 금지합니다.

    질문: {user_query}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    for i in range(5):
        try:
            res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=100)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0]['text']
                
                # [강력한 정제 로직] 
                # 1. 인용 태그 제거
                text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
                # 2. 대괄호로 둘러싸인 모든 시스템 라벨([위임법령 핵심] 등) 강제 제거
                text = re.sub(r"\[.*?\]", "", text)
                # 3. 금지 기호 제거
                text = text.replace("*", "").replace("/", "")
                
                return text.strip()
            time.sleep(2)
        except: continue
    return "시스템 응답에 실패했습니다. 잠시 후 다시 시도해 주세요."
