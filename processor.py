# processor.py
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st
import requests
import json
import time
import re

from engine import get_semantic_keywords, get_gemini_response
from database import get_ordinance_data
from storage import save_history


def handle_ai_analysis(user_query):
    """
    [UI-백엔드 브릿지 함수]
    app.py에서 이 함수만 호출하면 분석, DB탐색, 결과 저장까지 한 번에 끝냅니다.
    """
    # 1. 시맨틱 키워드 도출 (중요: 여기서 태그를 뽑아야 DB가 제13조를 찾습니다)
    semantic_tags = get_semantic_keywords(user_query)

    # 2. DB 탐색 (status와 context 확보)
    db_status, db_context = get_ordinance_data(user_query, semantic_tags)

    # 3. AI 응답 생성
    response_text = get_gemini_response(
        user_query=user_query,
        db_status=db_status,
        db_context=db_context,
        semantic_tags=semantic_tags
    )

    # 4. 대화방 방식으로 저장
    now = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")

    # chat_history가 없으면 빈 리스트 생성
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # selected_index가 없으면 None으로 생성
    if "selected_index" not in st.session_state:
        st.session_state.selected_index = None

    # 새 대화가 필요한 경우
    if st.session_state.selected_index is None or len(st.session_state.chat_history) == 0:
        new_chat = {
            "title": user_query[:20] + ("..." if len(user_query) > 20 else ""),
            "created_at": now,
            "updated_at": now,
            "messages": []
        }

        st.session_state.chat_history.append(new_chat)
        st.session_state.selected_index = len(st.session_state.chat_history) - 1

    # 현재 대화방 찾기
    current_chat = st.session_state.chat_history[st.session_state.selected_index]

    # 혹시 messages가 없으면 생성
    if "messages" not in current_chat:
        current_chat["messages"] = []

    # 현재 대화방 안에 질문/답변 추가
    current_chat["messages"].append({
        "query": user_query,
        "response": response_text,
        "time": now
    })

    current_chat["updated_at"] = now

    # 저장
    save_history(st.session_state.chat_history)

    return response_text


def fallback_civil_document(civil_type, site_address, civil_content):
    """
    Gemini 호출 실패 시에도 시연이 멈추지 않도록 제공하는 예비 민원서
    """
    return f"""
**민원 제목**

{civil_type} 관련 건축 민원

**민원 취지**

본 민원은 {site_address} 인근 대지의 건축물로 인해 발생한 생활환경 침해 우려에 대해 관할 행정기관의 확인과 검토를 요청하기 위한 것입니다.

민원인은 인접 대지의 건축 행위 또는 건축물로 인해 일조, 조망, 주거환경 등에 영향을 받고 있다고 판단하여, 해당 사안이 관련 법령 및 용인시 건축 관련 기준에 적합한지 검토를 요청드립니다.

**민원 내용**

대상 지역은 {site_address} 일대입니다.

민원 내용은 다음과 같습니다.

{civil_content}

현재 인접 대지 건축물로 인해 기존 주거지 또는 생활공간의 일조 확보에 지장이 발생하고 있는 것으로 보입니다. 이에 따라 해당 건축물의 배치, 높이, 이격거리 등이 관련 기준에 적합한지 확인이 필요합니다.

또한 해당 건축물의 허가 내용과 실제 시공 상태가 일치하는지, 주변 대지에 대한 영향 검토가 적절히 이루어졌는지도 확인해 주시기 바랍니다.

**요청사항**

위 민원 내용에 대해 현장 확인 및 관련 법령, 조례 기준에 따른 검토를 요청드립니다.

특히 인접 대지 건축물로 인한 일조권 침해 여부, 건축물 높이 및 이격거리 기준 적합 여부, 허가 내용과 실제 시공 상태의 일치 여부를 확인해 주시기 바랍니다.

검토 결과에 따라 필요한 행정 조치 가능 여부와 향후 처리 절차를 안내해 주시기 바랍니다.
"""


def format_civil_document_text(text):
    """
    Gemini가 제목과 내용을 한 줄로 붙여서 반환하더라도
    민원서 항목 제목을 볼드 처리하고 제목 뒤 줄바꿈을 강제합니다.
    """
    if not text:
        return text

    # 코드블록, 불필요한 마크다운 기호 정리
    text = text.replace("```markdown", "").replace("```", "").strip()
    text = text.replace("###", "").replace("**", "").replace("*", "").strip()

    # 혹시 AI가 예전 템플릿 명칭으로 반환하는 경우도 일부 정리
    heading_aliases = [
        ("민원 제목", "민원 제목"),
        ("민원 취지", "민원 취지"),
        ("민원 내용", "민원 내용"),
        ("요청사항", "요청사항"),
        ("요청 사항", "요청사항"),
        ("민원 요지 및 요청사항", "요청사항"),
    ]

    for raw_heading, display_heading in heading_aliases:
        text = re.sub(
            rf"(?<!\S)(?:\d+\.\s*)?{re.escape(raw_heading)}\s*[:：]?\s*",
            f"\n\n**{display_heading}**\n\n",
            text
        )

    # 빈 줄 과다 정리
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    return text


# 민원 생성용 LLM 호출 함수
def llm_invoke_function(system_prompt, user_prompt, civil_type, site_address, civil_content):
    """
    민원 양식 생성 전용 Gemini 호출 함수
    기존 AI 엔진을 활용하되, 민원서 작성용 프롬프트를 별도로 적용합니다.
    """
    try:
        MODEL_NAME = "gemini-2.5-flash"
        api_key = st.secrets["GEMINI_API_KEY"]

        url = f"https://generativelanguage.googleapis.com/v1/models/{MODEL_NAME}:generateContent?key={api_key}"

        headers = {
            "Content-Type": "application/json"
        }

        prompt = f"""
{system_prompt}

[사용자 입력]
{user_prompt}
"""

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        for i in range(5):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    data=json.dumps(payload),
                    timeout=100
                )

                if response.status_code == 200:
                    result_text = response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    return format_civil_document_text(result_text)

                time.sleep(2)

            except Exception:
                time.sleep(2)

    except Exception:
        pass

    # Gemini 호출 실패 시에도 앱이 빨간 오류로 터지지 않도록 예비 문서 반환
    return fallback_civil_document(civil_type, site_address, civil_content)


# 민원 생성 함수
def generate_civil_document(civil_type, site_address, civil_content):
    """
    민원 양식 전용 생성 함수
    PPT 17p의 '민원 제목 - 민원 취지 - 민원 내용 - 요청사항' 구조에 맞춰 생성합니다.
    """

    system_prompt = f"""
당신은 용인시청 건축부서에 제출할 민원서를 작성하는 전문 행정사입니다.
사용자의 입력 정보를 바탕으로 '오직 민원서 양식'만 작성하여 바로 출력하세요.

[작성 규칙]
1. 반드시 아래 템플릿의 1번부터 4번까지만 작성하세요.
2. 필요 서류 안내, 예상 담당 부서 안내, 민원 접수 방법, 민원 처리 상태 조회 방법, 다운로드 안내는 절대 작성하지 마세요.
3. 위 항목들은 화면 아래에서 별도로 제공되므로, 여기서는 민원서 본문만 작성하세요.
4. 각 항목 제목은 반드시 다음 네 가지 표현만 사용하세요: 민원 제목, 민원 취지, 민원 내용, 요청사항
5. 각 제목 뒤에는 반드시 줄바꿈을 넣고, 그 다음 줄부터 내용을 작성하세요.
6. 어조는 정중하고 객관적인 행정 문체를 사용하세요.
7. 사용자가 입력한 민원 내용을 반드시 반영하되, 사실관계를 과장하거나 확정적으로 단정하지 마세요.
8. 내용은 너무 짧게 끝내지 말고, 행정기관에 제출할 수 있을 정도로 구체적으로 작성하세요.
9. 법규 위반이라고 단정하지 말고, '검토를 요청드립니다', '확인이 필요합니다'와 같은 표현을 사용하세요.
10. 별표(*)나 이모지는 사용하지 마세요.

[민원서 템플릿]
민원 제목
{civil_type} 관련 건축 민원

민원 취지
{site_address} 인근에서 발생한 건축 관련 민원 제기의 목적을 2~3문장으로 작성하세요.

민원 내용
사용자가 입력한 내용을 바탕으로 구체적인 상황 설명을 작성하세요.
입력된 민원 내용: {civil_content}

요청사항
관할 행정기관에 요청하는 내용을 2~4문장으로 작성하세요.
현장 확인, 관련 법령 및 조례 기준 검토, 조치 가능 여부 안내, 향후 처리 절차 안내를 포함하세요.
"""

    user_prompt = f"""
민원 유형: {civil_type}
대상 건축물 주소: {site_address}
민원 내용: {civil_content}

위 내용을 바탕으로 용인시 건축 민원서 초안을 작성해줘.
"""

    return llm_invoke_function(
        system_prompt,
        user_prompt,
        civil_type,
        site_address,
        civil_content
    )
