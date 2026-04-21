import google.generativeai as genai
import re

def get_gemini_response(user_query):
    # 제공해주신 API 키를 직접 설정합니다
    genai.configure(api_key="AIzaSyAbu0meqf6IgTe68_cAljCGdOK21ldxQMg")
    
    # 모델 설정
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 인공지능 응답 지침 (별표나 슬래시 사용 금지)
    system_instruction = """
    당신은 용인시 건축 조례 전문가입니다. 
    데이터베이스에 없는 내용이라도 당신이 가진 건축 지식을 바탕으로 답변하세요.
    모든 답변은 반드시 다음 6개 항목에 맞춰 한국어로 작성하세요.
    항목 구분 시 별표나 슬래시 같은 특수 기호를 사용하지 마세요.
    답변 내용에 cite 문구나 인용 표시를 절대 포함하지 마세요.

    1. 결론
    2. 적용 지역
    3. 핵심 근거 조문
    4. 세부 설명
    5. 추가 확인 항목
    6. 담당 기관 및 후속 절차
    """
    
    full_prompt = f"{system_instruction}\n\n사용자 질문: {user_query}"
    
    try:
        response = model.generate_content(full_prompt)
        text = response.text
        
        # 인용구 및 불필요한 강조 기호 제거
        clean_text = re.sub(r"\[?cite:\s?\d+\]?", "", text)
        clean_text = clean_text.replace("*", "").replace("/", "")
        
        return clean_text
    except Exception as e:
        return f"인공지능 분석 중 오류가 발생했습니다: {str(e)}"
