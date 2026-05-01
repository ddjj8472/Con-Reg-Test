# engine.py
import streamlit as st
import requests
import json
import re
import time

def get_semantic_keywords(user_query):
    """[Step 1] 질문 분석을 통해 법률 검색용 단어를 도출합니다."""
    MODEL_NAME = "gemini-2.5-flash"
    api_key = st.secrets["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    analysis_prompt = f"질문: '{user_query}' / 이 질문과 관련된 대한민국 법령 명칭과 핵심 전문 용어를 콤마(,)로 구분해서 5개만 나열해줘."
    payload = {"contents": [{"parts": [{"text": analysis_prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except:
        return ""
    return ""

def get_gemini_response(user_query, db_status, db_context, semantic_tags=""):
    """
    [Step 2] 최종 답변 생성: 
    - 3개 항목 체제 (결론, 핵심 근거, 세부 해석)
    - 태그 노출 금지 및 표(Table) 생성 금지
    - 데이터 부족 시 일반 지식 보완 안내 문구 강제
    """
    MODEL_NAME = "gemini-2.5-flash" 
    api_key = st.secrets["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    # 데이터 충실도에 따른 대응 지침
    if db_status in ["INCOMPLETE", "NO_DATA"]:
        status_instruction = """
        [데이터 보충 지침]
        현재 DB에 직접적인 정보가 부족합니다.
        1. '세부 해석' 섹션 가장 첫 줄에 다음 문구를 반드시 포함하십시오: 
           "현재 데이터베이스만으로는 정보 제공이 완료될 수 없어 일반 지식을 사용하여 답변합니다."
        2. 그 후 당신의 전문 지식을 활용해 질문에 대한 상세한 해답을 작성하십시오.
        """
    else:
        status_instruction = "제공된 데이터베이스 내용을 바탕으로 전문적인 해석을 수행하십시오."

    prompt = f"""
    당신은 대한민국 건축/도시계획 행정 전문가입니다. 
    다음 지침에 따라 질문에 답변하십시오.

    {status_instruction}

    [참조용 시맨틱 태그]: {semantic_tags}
    [참조용 법규 데이터]:
    {db_context}

    보고서 구성 및 금지 규칙:
    1. 인삿말을 생략하고 바로 본론(항목)으로 시작하십시오.
    2. 다음 3개 항목으로만 구성하십시오:
       ### 결론
       (질문에 대한 핵심 요약)
       ### 핵심 근거
       (DB 내 관련 조문 또는 상위 법령 명칭)
       ### 세부 해석
       (DB 분석 내용 및 일반 지식을 활용한 상세 설명)
    3. 금지 사항: 
       - '원문 링크', '적용 지역', '담당 기관' 항목을 작성하지 마십시오.
       - '[법률 분석 태그]'와 같은 문구를 절대 본문에 노출하지 마십시오.
       - 표(Table)나 차트를 절대 만들지 마십시오. 오직 텍스트로만 설명하십시오.
       - 별표(*)와 슬래시(/)를 절대 사용하지 마십시오.

    질문: {user_query}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    for i in range(5):
        try:
            res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=100)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0]['text']
                # 정제: 금지 기호 및 불필요한 인용구 제거
                text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
                text = text.replace("*", "").replace("/", "")
                # 법률 분석 태그 관련 잔여 문구 제거
                text = text.replace("[법률 분석 태그]:", "").replace("법률 분석 태그:", "")
                return text
            time.sleep(2)
        except:
            continue
    return "AI 엔진 응답에 실패했습니다."
