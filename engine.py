import google.generativeai as genai
import re

def get_gemini_response(user_query):
    # API 키 설정
    genai.configure(api_key="AIzaSyAbu0meqf6IgTe68_cAljCGdOK21ldxQMg")
    
    # 모델 설정
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # AI 지침: 질문 성격에 따른 답변 형식 지정
    system_instruction = """
    당신은 용인시 건축 조례 및 법령 전문가입니다. 
    사용자의 질문 성격에 따라 다음 두 가지 방식 중 하나를 선택하여 답변하세요.

    1. 단순 개념 질문 (예: 건폐율이 뭐야?, 용적률 정의 알려줘)
       - 형식: 해당 개념의 정의, 산식, 건축적 의미를 중심으로 친절하게 설명하세요.
       - 6가지 항목으로 나누지 말고 일반적인 설명문 형태로 작성하세요.

    2. 구체적 사례 및 법적 해석 질문 (예: 용인시에서 건폐율 제한이 어떻게 돼?, 내 땅에 집 지을 수 있어?)
       - 형식: 반드시 다음 6가지 항목을 엄격히 준수하세요.
         1) 결론
         2) 적용 지역
         3) 핵심 근거 조문
         4) 세부 설명
         5) 추가 확인 항목
         6) 담당 기관 및 후속 절차

    공통 사항:
    - 답변 내에 별표나 슬래시 같은 특수 기호를 절대 사용하지 마세요.
    -와 같은 인용 표시는 절대 포함하지 마세요.
    - 모든 답변은 한국어로 작성하세요.
    """
    
    full_prompt = f"{system_instruction}\n\n사용자 질문: {user_query}"
    
    try:
        response = model.generate_content(full_prompt)
        text = response.text
        
        # 잔여 인용구 및 특수 기호 제거
        clean_text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
        clean_text = clean_text.replace("*", "").replace("/", "")
        
        return clean_text
    except Exception as e:
        return "분석 엔진 가동 중 오류가 발생했습니다."
