import streamlit as st

import requests

import json

import re



def get_gemini_response(user_query, db_context=""):

    try:

        api_key = st.secrets["GEMINI_API_KEY"]

        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"

        

        headers = {'Content-Type': 'application/json'}

        

        # [수정 포인트] 질문 성격에 따른 출력 형식 분기 지침 추가

        prompt = f"""

        당신은 용인시 건축 조례 및 법령 전문가입니다. 

        제공된 [참고 법규 데이터]를 최우선 근거로 사용하여 답변하십시오.



        [참고 법규 데이터]:

        {db_context if db_context else "직접적인 조례 데이터를 찾지 못했습니다. 일반적인 건축법령 지식에 기반하되 공식 확인이 필요함을 명시하십시오."}



        답변 규칙:

        1. 별표(*)와 슬래시(/)는 절대 사용하지 마십시오.

        2. 질문의 성격에 따라 형식을 달리하십시오:

           - [사례 해석 및 규제 확인]: 구체적인 대지 조건이나 행위에 대한 질문은 반드시 아래 '6개 항목'을 지키십시오.

           - [단순 개념 및 용어 정의]: "용적률이 뭐야?"와 같은 단순 질문은 6개 항목을 따르지 말고, 가독성 좋은 일반 설명문 형식으로 답변하십시오.

        3. 6개 항목 구성 (사례 질문용):

           1. 결론

           2. 적용 지역 및 법적 위계

           3. 핵심 근거 조문

           4. 세부 해석 및 설명

           5. 추가 확인 사항 및 원문 링크 (제공된 link 활용)

           6. 담당 기관 및 후속 절차



        질문: {user_query}

        """

        

        payload = {"contents": [{"parts": [{"text": prompt}]}]}

        # 복잡한 추론을 위해 타임아웃 60초 유지

        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)

        

        if response.status_code == 200:

            text = response.json()['candidates'][0]['content']['parts'][0]['text']

            # 불필요한 기호 제거 정제

            text = re.sub(r"\[?cite:\s?\d+\]?", "", text)

            text = text.replace("*", "").replace("/", "")

            return text

        else:

            return f"엔진 응답 실패: {response.status_code} / {response.text}"

            

    except Exception as e:

        return f"통신 장애 발생: {str(e)}"
