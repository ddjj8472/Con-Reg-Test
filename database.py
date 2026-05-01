import pandas as pd
import re
import os
import streamlit as st

# [성능 최적화] 데이터를 메모리에 미리 로드하여 검색 속도 향상
@st.cache_data
def load_all_databases():
    def safe_read_csv(file_path):
        encodings = ['utf-8-sig', 'cp949', 'utf-8', 'euc-kr']
        for enc in encodings:
            try:
                return pd.read_csv(file_path, encoding=enc)
            except:
                continue
        return None

    db_files = ["ordinance_basic.csv", "statute.csv", "ord_borrowed.csv", "stat_borrowed.csv"]
    db_dict = {}
    for f in db_files:
        if os.path.exists(f):
            df = safe_read_csv(f)
            if df is not None:
                db_dict[f] = df.fillna("")
    return db_dict

def get_ordinance_data(query):
    dbs = load_all_databases()
    if not dbs:
        return "데이터베이스 파일을 찾을 수 없습니다."

    # 1. 파일별 열 이름 스키마 정의
    file_configs = {
        "ordinance_basic.csv": {"name": "ordinance (조례명)", "content": "content", "link": "link", "category": "Category (주제)"},
        "statute.csv": {"name": "Ordinance(법규명)", "content": "Content(원문)", "link": "Link (원문링크)", "category": "Category (주제)"},
        "ord_borrowed.csv": {"name": "Ordinance(법규명)", "content": "Content(원문)", "link": "Link (원문링크)", "category": "Category (주제)"},
        "stat_borrowed.csv": {"name": "Ordinance(법규명)", "content": "Content(원문)", "link": "Link (원문링크)", "category": "Category (주제)"}
    }

    # 2. 키워드 분석 및 다중 키워드 AND 검색 준비
    keywords = query.split()
    is_urban_planning = any(kw in query for kw in ["용적률", "건폐율", "용도지역", "지구단위"])

    final_context = []
    processed_articles = set() # 중복 답변 방지

    # 3. [Tier 1] 핵심 6대 법령 정의 및 우선순위 설정
    tier1_names = [
        "용인시 건축 조례", "용인시 도시계획 조례", 
        "건축법", "건축법 시행령", 
        "국토의 계획 및 이용에 관한 법률", "국토의 계획 및 이용에 관한 법률 시행령"
    ]
    
    # 도시계획 관련 질문일 경우 도시계획 조례를 최상단으로
    if is_urban_planning:
        tier1_names.insert(0, tier1_names.pop(tier1_names.index("용인시 도시계획 조례")))

    # 4. [검색 엔진] 폭포수형 탐색 실행
    def search_in_files(file_list, label):
        for f_name in file_list:
            if f_name not in dbs: continue
            df = dbs[f_name]
            cfg = file_configs[f_name]
            
            # 다중 키워드 AND 검색 로직
            mask = df[cfg['content']].str.contains(keywords[0], na=False, case=False)
            for kw in keywords[1:]:
                mask &= df[cfg['content']].str.contains(kw, na=False, case=False)
            
            res = df[mask]
            print(f"--- [검색 로그] 파일: {f_name} | 검색어: {keywords} | 결과 수: {len(res)} ---")
            for _, row in res.iterrows():
                art_name = row[cfg['name']]
                if art_name in processed_articles: continue
                
                # 조문 스니핑 (핵심 내용 절삭)
                snip = extract_article_snip(row[cfg['content']], keywords[0])
                final_context.append(
                    f"### [{label}] {art_name}\n"
                    f"(분류: {row.get(cfg['category'], '일반')})\n{snip}\n"
                    f"링크: {row.get(cfg['link'], '정보 없음')}"
                )
                processed_articles.add(art_name)
                if len(final_context) >= 5: break # 컨텍스트 과부하 방지

    # Tier 1 검색 (핵심 법령)
    # 6대 법령이 포함된 행만 먼저 골라냄
    for f_key in ["ordinance_basic.csv", "statute.csv"]:
        if f_key in dbs:
            df = dbs[f_key]
            cfg = file_configs[f_key]
            tier1_df = df[df[cfg['name']].isin(tier1_names)]
            
            # AND 검색 적용
            mask = tier1_df[cfg['content']].str.contains(keywords[0], na=False, case=False)
            for kw in keywords[1:]:
                mask &= tier1_df[cfg['content']].str.contains(kw, na=False, case=False)
            
            res = tier1_df[mask]
            for _, row in res.iterrows():
                snip = extract_article_snip(row[cfg['content']], keywords[0])
                final_context.append(f"### [최우선 근거: 핵심 법령] {row[cfg['name']]}\n{snip}")
                processed_articles.add(row[cfg['name']])

    # Tier 2 & 3 검색 (나머지 전체 및 차용 법규)
    if len(final_context) < 3: # 핵심 법령에서 충분히 안 나왔을 때만 확장
        search_in_files(["ordinance_basic.csv", "statute.csv"], "추가 참고 법규")
        search_in_files(["ord_borrowed.csv", "stat_borrowed.csv"], "연관/차용 법리")

    return "\n\n---\n\n".join(final_context) if final_context else None

def extract_article_snip(text, keyword):
    if pd.isna(text) or not text: return ""
    # 제N조 패턴 찾기
    pattern = r"제\d+조(?:의\d+)?\s*\(.*?\)"
    articles = list(re.finditer(pattern, text))
    hit = text.find(keyword)
    if hit == -1: return text[:1500]
    
    start_pos, end_pos = 0, len(text)
    for i, art in enumerate(articles):
        if art.start() <= hit:
            start_pos = art.start()
            if i + 1 < len(articles):
                end_pos = articles[i+1].start()
        else:
            break
    return text[start_pos:end_pos][:2000]
