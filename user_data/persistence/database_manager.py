# src/persistence/database_manager.py
import sqlite3, json
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_url=None):
        # "sqlite:///./trade_reflection.db" → 파일 경로만 추출
        path = db_url.replace("sqlite:///", "")
        self.conn = sqlite3.connect(path)
        # trades, trading_reflection 테이블이 없으면 생성
        self.conn.execute("""
          CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME,
            data TEXT
          )""")
        self.conn.execute("""
          CREATE TABLE IF NOT EXISTS trading_reflection (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME,
            data TEXT
          )""")
        self.conn.commit()

    def record_trade(self, trade):
        ts = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute(
          "INSERT INTO trades (timestamp, data) VALUES (?, ?)",
          (ts, json.dumps(trade))
        )
        self.conn.commit()
        return cur.lastrowid

    def get_recent_trades(self, limit):
        cur = self.conn.cursor()
        cur.execute(
          "SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?",
          (limit,)
        )
        return cur.fetchall()

    def add_reflection(self, data):
        ts = datetime.utcnow().isoformat()
        cur = self.conn.cursor()
        cur.execute(
          "INSERT INTO trading_reflection (timestamp, data) VALUES (?, ?)",
          (ts, json.dumps(data))
        )
        self.conn.commit()
        return cur.lastrowid

    def get_reflection_history(self, limit):
        cur = self.conn.cursor()
        cur.execute(
          "SELECT * FROM trading_reflection ORDER BY timestamp DESC LIMIT ?",
          (limit,)
        )
        return cur.fetchall()
