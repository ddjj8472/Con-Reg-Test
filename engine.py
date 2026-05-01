import streamlit as st
import requests
import json
import re
import time

def get_semantic_keywords(user_query):
    """
    [Step 1] 시맨틱 레이어: 질문을 분석하여 법률적 단서(태그)를 도출합니다.
    데이터베이스 검색 전, AI가 '어떤 법령을 찾아야 할지' 전략을 짜는 단계입니다.
    """
    MODEL_NAME = "gemini-2.5-flash"
    api_key = st.secrets["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    
    analysis_prompt = f"""
    질문: '{user_query}'
    위 질문을 분석하여 대한민국 법규 데이터베이스에서 정보를 찾기 위한 핵심 검색어 5개를 뽑아주세요.
    반드시 관련 법령 명칭(예: 건축물관리법, 주차장법 등)과 행정 전문 용어(예: 사용승인일, 용도변경 등)를 포함해야 합니다.
    결과는 반드시 콤마(,)로만 구분된 단어 리스트로 출력하십시오. 
    예시: 건축물관리법,정기점검,사용승인일,유지관리,안전점검
    """
    
    payload = {"contents": [{"parts": [{"text": analysis_prompt}]}]}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        if response.status_code == 200:
            result = response.json()
            tags = result['candidates'][0]['content']['parts'][0]['text']
            return tags.strip()
    except Exception:
        return "" # 분석 실패 시 빈 문자열을 반환하여 기본 검색으로 진행
    return ""

def get_gemini_response(user_query, db_status, db_context, semantic_tags=""):
    """
    [Step 2] 최종 답변 생성: DB의 충실도(status)에 따라 지능적으로 대응합니다.
    """
    MODEL_NAME = "gemini-2.5-flash" 
    
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        
        # [데이터 충실도에 따른 동적 지침 설정]
        if db_status in ["INCOMPLETE", "NO_DATA"]:
            status_instruction = """
            [경고: 데이터 충실도 부족]
            제공된 법규 데이터가 질문에 답하기에 불충분하거나 직접적인 해답이 없습니다.
            반드시 '세부 해석' 섹션 시작 부분에 다음 문구를 토씨 하나 틀리지 말고 명시하십시오:
            "현재 데이터베이스만으로는 정보 제공이 완료될 수 없어 일반 지식을 사용하여 답변합니다."
            그 후, [법률 분석 태그]와 당신의 전문 지식을 활용하여 민원인의 질문에 대한 직접적인 해답을 상세히 보완하십시오.
            """
        else:
            status_instruction = "제공된 데이터베이스의 정보가 충분하므로, 이를 최우선 근거로 삼아 전문적인 법리 해석을 수행하십시오."

        prompt = f"""
        당신은 '용인시 건축 행정 전문가' AI입니다. 
        [법률 분석 태그]와 [참고 법규 데이터]를 바탕으로 민원인에게 답변하십시오.

        {status_instruction}

        [법률 분석 태그]: {semantic_tags}
        [참고 법규 데이터]:
        {db_context if db_context else "직접적인 조문을 찾지 못했습니다."}

        답변 규칙:
        1. 6개 항목 필수 구성: 결론, 적용 지역, 핵심 근거, 세부 해석, 원문 링크, 담당 기관.
        2. 별표(*)와 슬래시(/)는 절대 사용하지 마십시오. 가독성을 위해 줄바꿈과 명확한 문장을 사용하십시오.
        3. 핵심 근거에는 DB에서 찾은 간접 조문이라도 반드시 명기하여 법적 근거의 연결고리를 보여주십시오.

        질문: {user_query}
        """
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        # [안정성] 자동 재시도 및 오류 처리 로직
        max_retries = 5 
        for i in range(max_retries):
            try:
                response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=100)
                
                if response.status_code == 200:
                    result = response.json()
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    # 특수 태그 및 금지 기호 정제
                    text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
                    text = text.replace("*", "").replace("/", "")
                    return text
                
                if response.status_code == 429: # Rate Limit
                    time.sleep(2)
                    continue

                if response.status_code == 503: # Overload
                    if i < max_retries - 1:
                        time.sleep((i + 1) * 3)
                        continue
                
                return f"엔진 응답 실패: {response.status_code}"
                
            except requests.exceptions.Timeout:
                if i < max_retries - 1:
                    time.sleep(3)
                    continue
                return "엔진 응답 시간 초과. 잠시 후 다시 시도해 주세요."

    except Exception as e:
        return f"통신 장애 발생: {str(e)}"
