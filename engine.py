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
    - 도입 문구, 적용 지역, 담당 기관 삭제 (4개 항목 체제)
    - 데이터 부족 시 일반 지식 결합 강제
    """
    MODEL_NAME = "gemini-2.5-flash" 
    api_key = st.secrets["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    # 데이터 충실도에 따른 대응 지침 최적화
    if db_status in ["INCOMPLETE", "NO_DATA"]:
        # 데이터가 부족할 때 AI가 '모른다'고 하지 않고 지식을 동원하게 함
        status_instruction = """
        [데이터 보충 지침]
        현재 DB에 직접적인 조문이 부족합니다. 
        1. 세부 해석 시작 시 "현재 데이터베이스만으로는 정보 제공이 완료될 수 없어 일반 지식을 사용하여 답변합니다."를 반드시 포함하십시오.
        2. 당신의 전문적인 법률 지식(택지개발촉진법, 도시개발법 등)을 총동원하여 두 사업의 차이점(사업 주체, 방식, 목적 등)을 상세히 설명하십시오.
        """
    else:
        status_instruction = "제공된 데이터베이스 내용을 바탕으로 전문적인 해석을 수행하십시오."

    prompt = f"""
    당신은 대한민국 건축/도시계획 행정 전문가입니다. 
    사용자의 질문에 대해 다음 지침에 따라 보고서 형식으로 답변하십시오.

    {status_instruction}

    [법률 분석 태그]: {semantic_tags}
    [참고 법규 데이터]:
    {db_context}

    보고서 구성 규칙 (필수):
    1. 도입 인사말("민원인님~")을 절대 하지 마십시오. 바로 본론으로 들어갑니다.
    2. 다음 4개 항목으로만 구성하십시오:
       - 결론: 질문에 대한 핵심 요약
       - 핵심 근거: DB 내 조문 또는 관련 상위 법령 명칭
       - 세부 해석: DB 내용 분석 + 일반 지식 기반의 상세 비교 설명
       - 원문 링크: 관련 법령 링크 (없을 경우 '정보 없음')
    3. '적용 지역' 및 '담당 기관' 항목은 절대 포함하지 마십시오.
    4. 별표(*)와 슬래시(/) 사용을 절대 금지합니다.

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
                return text
            time.sleep(2)
        except:
            continue
    return "AI 엔진 응답에 실패했습니다."
