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
    - 3개 항목 체제 (결론, 핵심 근거, 세부 해석) 엄격 준수
    - 전문가 자기소개 문구 및 요약 섹션 삭제
    - 데이터 부족 시 일반 지식 보완 안내 문구 강제 삽입
    """
    MODEL_NAME = "gemini-2.5-flash" 
    api_key = st.secrets["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    # 데이터 충실도에 따른 대응 지침
    if db_status in ["INCOMPLETE", "NO_DATA"]:
        status_instruction = """
        [데이터 보충 지침]
        현재 데이터베이스에 직접적인 정보가 부족하므로 다음을 반드시 이행하십시오:
        1. '### 세부 해석' 섹션의 첫 문장을 반드시 다음과 같이 시작하십시오: 
           "현재 데이터베이스만으로는 정보 제공이 완료될 수 없어 일반 지식을 사용하여 답변합니다."
        2. 그 후 당신의 법률적 지식을 활용해 상세히 답변하십시오.
        """
    else:
        status_instruction = "제공된 데이터베이스 내용을 최우선 근거로 사용하여 답변하십시오."

    prompt = f"""
    당신은 대한민국 건축 및 도시계획 행정 전문가 역할을 수행합니다. 
    사용자의 질문에 대해 아래 지침을 엄격히 준수하여 보고서 형식으로 답변하십시오.

    {status_instruction}

    [참조용 시맨틱 태그]: {semantic_tags}
    [참조용 법규 데이터]:
    {db_context}

    보고서 구성 및 금지 규칙:
    1. 답변 본문에 "전문가로서 답변드립니다" 또는 "저는 ~전문가입니다"와 같은 자기소개 문구를 절대 포함하지 마십시오. 
    2. 인사말 없이 바로 다음 3개 항목으로만 구성을 종료하십시오:
       ### 결론
       ### 핵심 근거
       ### 세부 해석
    3. 금지 사항: 
       - '주요 차이점 요약', '원문 링크', '적용 지역' 등 위 3개 외의 추가 항목을 만들지 마십시오.
       - '[참조용 시맨틱 태그]' 또는 '[법률 분석 태그]'와 같은 시스템 용어를 본문에 노출하지 마십시오.
       - 표(Table), 리스트 요약, 차트를 만들지 말고 줄글 형식으로 상세히 설명하십시오.
       - 별표(*)와 슬래시(/) 사용을 절대 금지합니다.

    질문: {user_query}
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    for i in range(5):
        try:
            res = requests.post(url, headers=headers, data=json.dumps(payload), timeout=100)
            if res.status_code == 200:
                text = res.json()['candidates'][0]['content']['parts'][0]['text']
                # 정제 로직: 불필요한 인용구 및 금지 기호 제거
                text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
                text = text.replace("*", "").replace("/", "")
                # 시스템 태그 관련 잔여 문구 제거
                text = text.replace("[참조용 시맨틱 태그]", "").replace("[법률 분석 태그]", "")
                return text.strip()
            time.sleep(2)
        except:
            continue
    return "AI 엔진 응답에 실패했습니다."
