import sqlite3
import hashlib
import datetime
import os

DB_PATH = "settings_history.db"

def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            config_hash TEXT,
            config_content TEXT
        )
    """)
    return conn

def add_settings_history(config_path):
    with open(config_path, "rb") as f:
        content = f.read()
    config_hash = hashlib.sha256(content).hexdigest()
    timestamp = datetime.datetime.utcnow().isoformat()
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO settings_history (timestamp, config_hash, config_content) VALUES (?, ?, ?)",
        (timestamp, config_hash, content.decode("utf-8"))
    )
    conn.commit()
    conn.close()

def get_history(limit=5):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, timestamp, config_hash FROM settings_history ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def rollback_config(target_id, config_path):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT config_content FROM settings_history WHERE id=?", (target_id,))
    row = cur.fetchone()
    if not row:
        raise ValueError("해당 이력 ID가 없습니다.")
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(row[0])
    conn.close()
    print(f"[✔] {target_id}번 이력으로 설정 롤백 완료.")
