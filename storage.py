# storage.py
import sqlite3
import json

DB_PATH = "platform_data.db"

def init_db():
    """데이터베이스 및 회원 정보, 대화 이력 테이블을 초기화합니다."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. 회원 정보 테이블 (아이디, 비밀번호)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)
    
    # 2. 대화 이력 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_history (
            user_id TEXT PRIMARY KEY,
            history_data TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    conn.commit()
    conn.close()

# 앱 실행 시 데이터베이스 시스템 초기화
init_db()

# --- 🔐 회원 관리 시스템 백엔드 로직 ---

def check_id_exists(user_id):
    """아이디 중복 검사를 수행합니다. 이미 존재하면 True, 없으면 False를 반환합니다."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def register_user(user_id, password):
    """새로운 회원을 등록합니다. 성공 시 True, 중복 발생 시 False를 반환합니다."""
    if check_id_exists(user_id):
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (user_id, password) VALUES (?, ?)", (user_id, password))
        conn.commit()
        success = True
    except:
        success = False
    finally:
        conn.close()
    return success

def authenticate_user(user_id, password):
    """로그인 인증을 수행합니다. 아이디와 비밀번호가 일치하면 True를 반환합니다."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE user_id = ? AND password = ?", (user_id, password))
    row = cursor.fetchone()
    conn.close()
    return row is not None

# --- 🗄️ 대화 이력 관리 백엔드 로직 ---

def load_history(user_id):
    """DB에서 특정 인증된 사용자의 대화 기록을 안전하게 판독합니다."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT history_data FROM user_history WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row[0])
    return []

def save_history(history_list, user_id):
    """인증된 사용자의 대화 기록 구조를 무결하게 저장 및 갱신합니다."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO user_history (user_id, history_data)
        VALUES (?, ?)
    """, (user_id, json.dumps(history_list, ensure_ascii=False, indent=2)))
    conn.commit()
    conn.close()

def clear_history(user_id):
    """DB 레코드에서 특정 인증 사용자의 대화 히스토리 라인만 삭제합니다."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_history WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
