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

def extract_smart_snip(text, query, semantic_tags="", intent_type="detail"):
    """
    [개선] 단순 키워드가 아닌, 실무적 키워드가 포함된 조항을 우선적으로 찾습니다.
    """
    if not text: return ""
    pattern = r"제\d+조(?:의\d+)?\s*\(.*?\)"
    articles = list(re.finditer(pattern, text))
    
    if intent_type == "overview" or not articles:
        return text[:(articles[3].start() if len(articles) > 3 else len(text))].strip()
    
    # [개선] 법령 명칭보다는 '점검', '시기', '기준' 같은 실무 키워드에 우선순위를 둡니다.
    search_keywords = [kw for kw in set(query.split() + semantic_tags.split(',')) if len(kw) > 1]
    # 법령 이름(ex: 건축물관리법)은 검색 우선순위에서 낮춰서 제1조 목적 함정을 피합니다.
    priority_keywords = [kw for kw in search_keywords if "법" not in kw and "조례" not in kw]
    if not priority_keywords: priority_keywords = search_keywords

    hit_pos = -1
    for kw in priority_keywords:
        pos = text.find(kw)
        if pos != -1:
            hit_pos = pos
            break
    
    if hit_pos == -1: return text[:1500]

    start_pos, end_pos = 0, len(text)
    for i, art in enumerate(articles):
        if art.start() <= hit_pos:
            start_pos = art.start()
            if i + 1 < len(articles): end_pos = articles[i+1].start()
        else: break
    return text[start_pos:end_pos].strip()

def get_ordinance_data(query, semantic_tags=""):
    dbs = load_all_databases()
    tags_list = [t.strip() for t in semantic_tags.split(',') if t.strip()]
    combined_keywords = [kw for kw in set(query.split() + tags_list) if len(kw) > 1]
    
    final_context, processed_sources, total_density_score = [], set(), 0
    SATISFACTION_THRESHOLD = 25 # [상향] 정보 밀도 임계치 상향

    tier_configs = [
        {"label": "조례 핵심", "file": "ordinance_basic.csv", "targets": ["용인시 건축물관리 조례", "용인시 건축 조례", "용인시 도시계획 조례"]},
        {"label": "위임법령 핵심", "file": "statute.csv", "targets": ["건축물관리법", "건축물관리법 시행령", "건축법", "건축법 시행령"]},
        {"label": "조례 일반", "file": "ordinance_basic.csv", "region": "용인"},
        {"label": "위임법령", "file": "statute.csv", "all": True},
        {"label": "연관 법리", "file": ["ord_borrowed.csv", "stat_borrowed.csv"], "all": True}
    ]

    for tier in tier_configs:
        # [개선] '핵심'이 들어간 티어는 점수가 찼더라도 일단 훑습니다.
        if total_density_score >= SATISFACTION_THRESHOLD and "핵심" not in tier["label"]:
            break
            
        files = [tier["file"]] if isinstance(tier["file"], str) else tier["file"]
        for f_name in files:
            if f_name not in dbs: continue
            df = dbs[f_name]
            name_col = "ordinance (조례명)" if "ordinance" in f_name else "Ordinance(법규명)"
            content_col = "content" if "content" in df.columns else "Content(원문)"
            
            # 필터링
            if "targets" in tier:
                target_df = df[df[name_col].isin(tier["targets"])]
            elif "region" in tier:
                target_df = df[df['region (지자체)'].str.contains(tier["region"], na=False) if 'region (지자체)' in df.columns else df.index == -1]
            else:
                target_df = df
            
            for _, row in target_df.iterrows():
                name = str(row[name_col])
                if name in processed_sources: continue
                content = str(row[content_col])
                
                if any(kw in name or kw in content for kw in combined_keywords):
                    score = sum(10 if kw in name else 2 for kw in combined_keywords if kw in name or kw in content)
                    # [개선] extract_smart_snip에 semantic_tags를 전달해 더 정확한 위치를 찾게 함
                    snip = extract_smart_snip(content, query, semantic_tags)
                    final_context.append(f"### [{tier['label']}] {name}\n{snip}")
                    processed_sources.add(name)
                    total_density_score += score
                    
                    if total_density_score >= 40: # 과도한 데이터 방지용 절대 상한선
                        break

    if not final_context: return "NO_DATA", "검색 결과 없음"
    status = "COMPLETE" if total_density_score >= SATISFACTION_THRESHOLD else "INCOMPLETE"
    return status, "\n\n---\n\n".join(final_context)
