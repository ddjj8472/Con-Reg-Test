import pandas as pd
import re
import os
import streamlit as st

@st.cache_data
def load_all_databases():
    def safe_read_csv(file_path):
        encodings = ['utf-8-sig', 'cp949', 'utf-8', 'euc-kr']
        for enc in encodings:
            try: return pd.read_csv(file_path, encoding=enc)
            except: continue
        return None
    db_files = ["ordinance_basic.csv", "statute.csv", "ord_borrowed.csv", "stat_borrowed.csv"]
    return {f: df.fillna("") for f in db_files if os.path.exists(f) and (df := safe_read_csv(f)) is not None}

def extract_smart_snip(text, query, semantic_tags=""):
    """
    조문 번호와 실무 키워드 밀도를 계산해 가장 가치 있는 조문을 우선 추출합니다.
    """
    if not text: return ""
    pattern = r"(제\d+조(?:의\d+)?\s*\(.*?\))"
    sections = re.split(pattern, text)
    articles = []
    if len(sections) > 1:
        for i in range(1, len(sections), 2):
            articles.append(sections[i] + (sections[i+1] if i+1 < len(sections) else ""))
    else: return text[:1500]

    keywords = [kw for kw in set(query.split() + semantic_tags.split(',')) if len(kw) > 1]
    # '목적', '정의' 보다는 구체적 실무 단어에 가중치
    priority_kws = [k for k in keywords if k not in ["법", "조례", "목적", "정의"]]

    scored_articles = []
    for art in articles:
        score = sum(20 if kw in art else 0 for kw in priority_kws)
        if score > 0: scored_articles.append((score, art.strip()))
    
    scored_articles.sort(key=lambda x: x[0], reverse=True)
    return "\n\n".join([art for _, art in scored_articles[:3]]) if scored_articles else articles[0][:1000]

def get_ordinance_data(query, semantic_tags=""):
    """
    [범용 해결책] 특정 점수 도달 시에도 '법령(Statute)' 및 '차용법규'는 
    반드시 전수 조사하도록 탐색 로직을 강화했습니다.
    """
    dbs = load_all_databases()
    tags_list = [t.strip() for t in semantic_tags.split(',') if t.strip()]
    combined_keywords = [kw for kw in set(query.split() + tags_list) if len(kw) > 1]
    
    final_context, processed_sources, total_density_score = [], set(), 0
    # 정보 밀도 목표치 (이 수치가 넘어도 핵심 파일은 계속 탐색함)
    SATISFACTION_THRESHOLD = 35 

    tier_configs = [
        {"label": "조례 핵심", "file": "ordinance_basic.csv", "keywords": ["용인", "건축 조례"]},
        {"label": "위임법령", "file": "statute.csv", "all": True},
        {"label": "차용/연관법규", "file": ["stat_borrowed.csv", "ord_borrowed.csv"], "all": True}
    ]

    for tier in tier_configs:
        # 핵심 조례 탐색 중 점수가 찼다면 넘어가지만, '위임법령'과 '차용법규'는 무조건 수행
        if total_density_score >= SATISFACTION_THRESHOLD and tier['label'] == "조례 핵심":
            continue
            
        files = [tier["file"]] if isinstance(tier["file"], str) else tier["file"]
        for f_name in files:
            if f_name not in dbs: continue
            df = dbs[f_name]
            name_col = "ordinance (조례명)" if "ordinance" in f_name else "Ordinance(법규명)"
            content_col = "content" if "content" in df.columns else "Content(원문)"
            
            # 티어별 매칭 수행
            for _, row in df.iterrows():
                name = str(row[name_col])
                if name in processed_sources: continue
                content = str(row[content_col])
                
                # 키워드 매칭 시 스니펫 추출
                if any(kw in name or kw in content for kw in combined_keywords):
                    snip = extract_smart_snip(content, query, semantic_tags)
                    if len(snip) > 30:
                        final_context.append(f"### [{tier['label']}] {name}\n{snip}")
                        processed_sources.add(name)
                        total_density_score += 15 # 조문 발견 시 가중치
                    
                    if total_density_score >= 80: break # 과부하 방지용 하드 리밋
    
    status = "COMPLETE" if total_density_score >= SATISFACTION_THRESHOLD else "INCOMPLETE"
    return status, "\n\n---\n\n".join(final_context)

@st.cache_data
def load_law_links():
    """link.csv 파일을 읽어 {법규명: 원문링크} 딕셔너리를 반환합니다."""
    path = "link.csv"
    if os.path.exists(path):
        try:
            # link.csv를 읽어 법규명과 링크를 매핑합니다.
            df = pd.read_csv(path, encoding='utf-8-sig')
            return dict(zip(df['법규명'], df['원문링크']))
        except:
            return {}
    return {}
