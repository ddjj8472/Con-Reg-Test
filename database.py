import pandas as pd
import re
import os

def get_ordinance_data(query):
    # 1. 파일별 열 이름 매핑 정보 (분석 결과 반영)
    file_configs = {
        "ordinance_basic.csv": {
            "name": "ordinance (조례명)",
            "content": "content",
            "link": "link",
            "category": "Category (주제)"
        },
        "statute.csv": {
            "name": "Ordinance(법규명)",
            "content": "Content(원문)",
            "link": "Link (원문링크)",
            "category": "Category (주제)"
        },
        "ord_borrowed.csv": {
            "name": "Ordinance(법규명)",
            "content": "Content(원문)",
            "link": "Link (원문링크)",
            "category": "Category (주제)"
        },
        "stat_borrowed.csv": {
            "name": "Ordinance(법규명)",
            "content": "Content(원문)",
            "link": "Link (원문링크)",
            "category": "Category (주제)"
        }
    }

    final_context = []
    
    def extract_article_snip(text, keyword):
        """방대한 원문에서 키워드가 포함된 특정 조문 구역만 잘라내는 함수"""
        if pd.isna(text) or not text: return ""
        # 조문 패턴: 제N조(제목) 또는 제N조의N(제목)
        pattern = r"제\d+조(?:의\d+)?\s*\(.*?\)"
        articles = list(re.finditer(pattern, text))
        hit = text.find(keyword)
        
        if hit == -1: return text[:2000] # 키워드 없으면 상단 출력
        
        start_pos, end_pos = 0, len(text)
        for i, art in enumerate(articles):
            if art.start() <= hit:
                start_pos = art.start()
                if i + 1 < len(articles):
                    end_pos = articles[i+1].start()
            else:
                break
        return text[start_pos:end_pos][:2500]

    try:
        # [Step 1] 조례 기본 DB에서 검색 시작
        f_basic = "ordinance_basic.csv"
        cfg_basic = file_configs[f_basic]
        
        if os.path.exists(f_basic):
            df_basic = pd.read_csv(f_basic, encoding='utf-8-sig')
            res_basic = df_basic[df_basic[cfg_basic['content']].str.contains(query, na=False, case=False)]
            
            if not res_basic.empty:
                row = res_basic.iloc[0]
                snip = extract_article_snip(row[cfg_basic['content']], query)
                final_context.append(
                    f"### [용인시 조례] {row[cfg_basic['name']]}\n"
                    f"(분류: {row[cfg_basic['category']]})\n{snip}\n"
                    f"출처: {row[cfg_basic['link']]}"
                )
                
                # [Step 2] 텍스트 내 「...」 법령명 추출하여 차용/연관 관계 추적
                refs = re.findall(r"「(.*?)」", snip)
                for ref_name in set(refs):
                    for f_other in ["statute.csv", "ord_borrowed.csv", "stat_borrowed.csv"]:
                        if os.path.exists(f_other):
                            cfg_other = file_configs[f_other]
                            df_other = pd.read_csv(f_other, encoding='utf-8-sig')
                            res_other = df_other[df_other[cfg_other['name']].str.contains(ref_name, na=False, case=False)]
                            
                            if not res_other.empty:
                                r_row = res_other.iloc[0]
                                r_content = r_row[cfg_other['content']]
                                # 차용 법령에서도 키워드 주변을 찾거나 상단을 가져옴
                                r_snip = extract_article_snip(r_content, query) if not pd.isna(r_content) else "내용 없음"
                                final_context.append(f"### [연관/차용 법규] {r_row[cfg_other['name']]}\n{r_snip}")
                                break

        # [Step 3] 조례에 결과가 없는 경우 상위 법령 DB 전수 조사
        if not final_context and os.path.exists("statute.csv"):
            cfg_stat = file_configs["statute.csv"]
            df_stat = pd.read_csv("statute.csv", encoding='utf-8-sig')
            res_stat = df_stat[df_stat[cfg_stat['content']].str.contains(query, na=False, case=False)]
            if not res_stat.empty:
                row = res_stat.iloc[0]
                final_context.append(f"### [상위 법령 직접 검색] {row[cfg_stat['name']]}\n{row[cfg_stat['content']][:2000]}")

    except Exception as e:
        return f"데이터베이스 탐색 중 오류 발생: {str(e)}"

    return "\n\n---\n\n".join(final_context) if final_context else None
