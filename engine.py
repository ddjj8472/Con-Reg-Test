import streamlit as st
import requests
import json
import re
import time

def get_gemini_response(user_query, db_context=""):
    # [복구] 최신 환경에 맞춘 모델 설정
    MODEL_NAME = "gemini-2.5-flash" 
    
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        
        # [프롬프트 개선] DB 한계 인정 및 일반 지식 보완 로직 강화
        prompt = f"""
        당신은 '용인시 건축 조례 전문 해석 AI 플랫폼'의 행정 전문가입니다. 
        사용자의 질문에 대해 제공된 [참고 법규 데이터]를 바탕으로 1차 분석을 수행하십시오.

        [참고 법규 데이터]:
        {db_context if db_context else "해당 질문과 관련된 직접적인 조문이 데이터베이스에 존재하지 않습니다."}

        답변 생성 가이드라인:
        1. [DB 한계 및 간접 정보 명기]: 
           - 제공된 데이터에 질문과 관련된 간접적인 언급이 있다면 반드시 '핵심 근거'와 '세부 해석'에 먼저 포함시키십시오.
           - 만약 데이터베이스의 정보만으로 질문에 대한 직접적이고 완전한 해답을 제공할 수 없는 경우, 반드시 답변 서두나 세부 해석 도입부에 다음 문구를 명시하십시오:
             "현재 데이터베이스만으로는 정보 제공이 완료될 수 없어 일반 지식을 사용하여 답변합니다."

        2. [일반 지식 보완]: 
           - 위 문구를 명시한 후, 당신이 보유한 전문적인 건축법령 및 행정 지식을 사용하여 질문에 대한 명확한 해답(예: 정의, 차이점 등)을 제공하십시오.

        3. [구조 및 형식]:
           - 별표(*)와 슬래시(/)는 절대 사용하지 마십시오.
           - 다음 6개 항목을 반드시 준수하여 구성하십시오:
             결론: (질문에 대한 핵심 요약)
             적용 지역: (법규의 적용 범위)
             핵심 근거: (DB 내 간접 조항 및 관련 상위 법령 명칭)
             세부 해석: (DB 내용 분석 + 정보 보완 안내 문구 + 일반 지식 기반 상세 설명)
             원문 링크: (정보가 있을 경우만 기재, 없으면 '정보 없음')
             담당 기관: (용인시 관련 부서 및 중앙행정기관)

        질문: {user_query}
        """
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        # [핵심] 자동 재시도 로직
        max_retries = 5 
        for i in range(max_retries):
            try:
                response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=100)
                
                if response.status_code == 200:
                    result = response.json()
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    # 불필요한 태그 및 금지 기호 제거
                    text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
                    text = text.replace("*", "").replace("/", "")
                    return text
                
                if response.status_code == 429:
                    # 유료 계정이라도 짧은 시간 내 과도한 요청 시 발생 가능
                    time.sleep(2)
                    continue

                if response.status_code == 503:
                    if i < max_retries - 1:
                        wait_time = (i + 1) * 3
                        time.sleep(wait_time)
                        continue
                
                return f"엔진 응답 실패: {response.status_code} / {response.text}"
                
            except requests.exceptions.Timeout:
                if i < max_retries - 1:
                    time.sleep(3)
                    continue
                return "엔진 응답 시간 초과 (100초). 다시 시도해 주세요."

    except Exception as e:
        return f"통신 장애 발생: {str(e)}"
