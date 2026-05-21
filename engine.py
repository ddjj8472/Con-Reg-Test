import re
from database import load_law_links
from database import load_sitemap_db

# =========================================================
# TEST ENGINE MODE
# ---------------------------------------------------------
# 발표/시연 중 Gemini 429, 503, API Key 문제로 앱이 멈추지 않도록
# 외부 LLM 호출 없이 고정된 형식의 답변을 반환하는 테스트 엔진입니다.
# =========================================================
TEST_MODE = True


def get_semantic_keywords(user_query):
    """[TEST] 질문에서 자주 쓰이는 건축 법규 키워드를 간단히 추출합니다."""
    keyword_map = {
        "일조": "일조권, 건축법 시행령, 용인시 건축 조례, 대지 안의 공지, 높이 제한",
        "건폐율": "건폐율, 용인시 도시계획 조례, 국토의 계획 및 이용에 관한 법률, 용도지역, 대지면적",
        "용적률": "용적률, 용인시 도시계획 조례, 국토의 계획 및 이용에 관한 법률, 용도지역, 연면적",
        "주차": "부설주차장, 주차장법, 용인시 주차장 조례, 시설 용도, 주차대수",
        "용도변경": "용도변경, 건축법, 건축물대장, 허가 신고, 건축물 용도",
        "건축선": "건축선, 도로, 접도, 건축법, 대지와 도로의 관계",
        "높이": "건축물 높이, 사선제한, 일조권, 건축법 시행령, 용도지역",
        "허가": "건축허가, 건축신고, 세움터, 건축법, 인허가 절차",
        "불법": "위반건축물, 이행강제금, 건축법, 현장조사, 시정명령",
    }

    found = []
    for key, tags in keyword_map.items():
        if key in user_query:
            found.append(tags)

    if found:
        return ", ".join(found)

    return "건축법, 용인시 건축 조례, 건축 인허가, 행정 민원, 건축물 기준"


def apply_law_links(text):
    """답변 본문에 등장한 법령명에 대해 기존 링크 DB를 활용해 원문 링크를 붙입니다."""
    link_db = load_law_links()
    if not link_db:
        return text

    found_links = []
    clean_text = re.sub(r'[\s\.\,\(\)\[\]]', '', text)
    sorted_law_names = sorted(link_db.keys(), key=len, reverse=True)

    for law_name in sorted_law_names:
        law_name_no_space = law_name.replace(" ", "")
        if law_name_no_space in clean_text:
            url = link_db[law_name].strip()

            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            link_entry = f"- [{law_name}]|||{url}|||"
            if link_entry not in found_links:
                found_links.append(link_entry)

    if found_links:
        link_section = "\n\n---\n\n### 🔗 관련 법령 원문 링크 (클릭 시 이동)\n\n" + "\n".join(found_links[:5])
        return text + link_section

    return text


def get_relevant_sitemap(user_query):
    """[TEST] LLM 없이 사이트맵 DB에서 질문 키워드와 겹치는 메뉴를 간단 매칭합니다."""
    df = load_sitemap_db()
    if df is None or df.empty:
        return ""

    query = re.sub(r"\s+", "", user_query.lower())
    scored = []

    for idx, row in df.iterrows():
        menu = str(row.get('menu (메뉴명)', '')).strip()
        function = str(row.get('function (기능)', '')).strip()
        link = str(row.get('link (링크)', '')).strip()
        haystack = re.sub(r"\s+", "", (menu + " " + function).lower())

        score = 0
        for token in ["건축", "허가", "신고", "주차", "용도", "민원", "도로", "일조", "불법", "대장"]:
            if token in query and token in haystack:
                score += 1

        if score > 0 and link:
            scored.append((score, idx, menu, link))

    scored.sort(reverse=True, key=lambda x: x[0])
    found_links = []

    for score, idx, menu, link in scored[:2]:
        if not link.startswith(('http://', 'https://')):
            link = 'https://' + link
        menu_name = menu.split(">")[-1].strip() if menu else "관련 행정 서비스"
        found_links.append(f"- **{menu_name} 안내 웹페이지 바로가기**: [{menu}]|||{link}|||")

    if found_links:
        return "\n\n---\n\n### 🏛️ 용인시청 홈페이지 행정 서비스 연계\n" + "\n".join(found_links)

    return ""


def _infer_topic(user_query):
    if "일조" in user_query or "높이" in user_query:
        return "일조권 및 건축물 높이 기준"
    if "건폐율" in user_query:
        return "건폐율 기준"
    if "용적률" in user_query:
        return "용적률 기준"
    if "주차" in user_query:
        return "부설주차장 설치 기준"
    if "용도변경" in user_query or "용도 변경" in user_query:
        return "건축물 용도변경 가능 여부"
    if "건축선" in user_query or "도로" in user_query or "접도" in user_query:
        return "건축선 및 접도 기준"
    if "불법" in user_query or "위반" in user_query:
        return "위반건축물 검토"
    if "허가" in user_query or "신고" in user_query:
        return "건축허가 및 신고 절차"
    return "건축 법규 검토"


def get_gemini_response(user_query, db_status, db_context, semantic_tags=""):
    """[TEST] 외부 API 호출 없이 법규 검토 형식의 테스트 답변을 반환합니다."""
    topic = _infer_topic(user_query)

    if db_status in ["COMPLETE", "FOUND"]:
        data_note = "내부 조례 데이터에서 관련성이 있는 항목이 일부 확인된 상태입니다."
    elif db_status in ["INCOMPLETE", "NO_DATA"]:
        data_note = "현재 입력 정보만으로는 세부 조건이 부족하므로, 실제 판단 전 담당 부서 확인이 필요합니다."
    else:
        data_note = "테스트 엔진 기준으로 일반적인 건축 행정 검토 흐름을 안내합니다."

    context_excerpt = ""
    if db_context:
        cleaned_context = re.sub(r"\s+", " ", str(db_context)).strip()
        context_excerpt = cleaned_context[:260]

    answer = f"""
### 결론
테스트 엔진 기준으로 볼 때, 이번 질문은 {topic}에 관한 사안입니다. 단정적인 허가 가능 여부보다는 용도지역, 대지 조건, 건축물 규모, 도로 접합 여부, 조례상 예외 기준을 함께 확인해야 합니다.

### 적용 지역
용인시를 기준으로 검토하는 테스트 답변입니다. 다만 실제 인허가 판단은 처인구, 기흥구, 수지구 등 관할 구청 또는 용인시 담당 부서의 최종 확인이 필요합니다.

### 핵심 근거
주요 검토 근거는 건축법, 건축법 시행령, 용인시 건축 조례, 용인시 도시계획 조례입니다. 질문 내용에 따라 주차장법, 국토의 계획 및 이용에 관한 법률, 건축물관리법 등이 추가로 검토될 수 있습니다.

### 세부 해석
{data_note}
질문 내용: {user_query}
추출 키워드: {semantic_tags or get_semantic_keywords(user_query)}
{('참고 데이터 요약: ' + context_excerpt) if context_excerpt else '참고 데이터 요약: 현재 테스트 모드에서는 상세 원문 대신 검토 흐름 중심으로 답변합니다.'}

실무적으로는 먼저 대상지의 용도지역과 건축물 용도를 확인하고, 그 다음 건축법상 일반 기준과 용인시 조례의 위임 기준을 비교해야 합니다. 조례가 수치 기준이나 세부 절차를 별도로 정한 경우에는 상위법의 범위 안에서 조례 기준을 함께 적용해야 합니다.

### 원문 링크
아래 관련 법령 링크는 내부 링크 DB에 존재하는 경우 자동으로 추가됩니다. 링크가 표시되지 않으면 법제처 국가법령정보센터 또는 자치법규정보시스템에서 법령명을 직접 검색하면 됩니다.

### 담당 기관
일반적인 건축허가, 신고, 용도변경, 위반건축물 확인은 관할 구청 건축허가과 또는 건축과 확인이 필요합니다. 도시계획 조례, 용도지역, 지구단위계획 관련 쟁점은 도시계획 담당 부서 확인이 함께 필요할 수 있습니다.
""".strip()

    final_text = apply_law_links(answer)
    sitemap_text = get_relevant_sitemap(user_query)
    return final_text + sitemap_text
