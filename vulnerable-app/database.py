import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config

def get_db_connection():
    """데이터베이스 연결"""
    return psycopg2.connect(Config.DATABASE_URL)

def get_user_by_username(username):
    """사용자명으로 사용자 정보 조회"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, username, email, phone_num, address FROM users WHERE username = %s",
                (username,)
            )
            return cur.fetchone()
    finally:
        conn.close()

def get_user_by_id(user_id):
    """ID로 사용자 정보 조회"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, username, email, phone_num, address FROM users WHERE id = %s",
                (user_id,)
            )
            return cur.fetchone()
    finally:
        conn.close()

def create_user(username, password_hash, email, phone_num=None, address=None):
    """새 사용자 생성"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """INSERT INTO users (username, password_hash, email, phone_num, address) 
                   VALUES (%s, %s, %s, %s, %s) 
                   RETURNING id, username, email, phone_num, address""",
                (username, password_hash, email, phone_num, address)
            )
            new_user = cur.fetchone()
            conn.commit()
            return new_user
    finally:
        conn.close()

