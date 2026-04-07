import mysql.connector
from mysql.connector import pooling
from contextlib import contextmanager
from config import settings

mysql_pool = pooling.MySQLConnectionPool(**settings.MYSQL_CONFIG)

@contextmanager
def get_mysql_connection():
    conn = mysql_pool.get_connection()
    try:
        yield conn
    finally:
        conn.close()

def get_user_by_username(username: str):
    with get_mysql_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT uuid, username, password_hash, nickname, avatar FROM users WHERE username = %s AND is_active = 1",
            (username,)
        )
        user = cursor.fetchone()
        cursor.close()
        return user

def get_user_by_uuid(user_uuid: str):
    with get_mysql_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT uuid, username, nickname, avatar, email FROM users WHERE uuid = %s AND is_active = 1",
            (user_uuid,)
        )
        user = cursor.fetchone()
        cursor.close()
        return user

def create_user(username: str, password_hash: str, email: str = None, nickname: str = None):
    import uuid
    user_uuid = str(uuid.uuid4())
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (uuid, username, password_hash, email, nickname) VALUES (%s, %s, %s, %s, %s)",
            (user_uuid, username, password_hash, email, nickname or username)
        )
        conn.commit()
        cursor.close()
        return user_uuid

def update_last_login(user_uuid: str):
    from datetime import datetime
    with get_mysql_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET last_login_at = %s WHERE uuid = %s",
            (datetime.now(), user_uuid)
        )
        conn.commit()
        cursor.close()
