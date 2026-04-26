import json
import os

FILE_PATH = "history.json"

def load_history():
    """파일에서 전체 대화 기록을 가져옵니다."""
    if not os.path.exists(FILE_PATH):
        return []
    try:
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # 파일이 비어있거나 손상되었을 경우 빈 리스트 반환
        return []

def save_history(history_list):
    """업데이트된 전체 기록을 파일에 영구 저장합니다."""
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(history_list, f, ensure_ascii=False, indent=2)

def clear_history():
    """모든 기록을 지우고 빈 파일로 초기화합니다."""
    save_history([])
