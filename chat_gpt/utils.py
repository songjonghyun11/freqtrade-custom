# ===== /home/stongone123/freqtrade/src/utils/risk_manager.py 시작 =====
# strategy/modules/risk_manager.py

class RiskManager:
    def __init__(self, stoploss_atr_multiplier: float):
        self.sl_multiplier = stoploss_atr_multiplier

    def calculate_stoploss(self, entry_price: float, atr: float) -> float:
        """
        동적 손절가 계산: entry_price - sl_multiplier * atr
        """
        return entry_price - self.sl_multiplier * atr

    def should_abort(self, portfolio_drawdown: float, max_dd: float) -> bool:
        """
        포트폴리오 MDD 기반 중단 여부
        """
        return portfolio_drawdown >= max_dd

# ===== /home/stongone123/freqtrade/src/utils/risk_manager.py 끝 =====

# ===== /home/stongone123/freqtrade/src/utils/entry_signal.py 시작 =====
# modules/entry_signal.py
import pandas as pd

class EntrySignal:
    def __init__(self, params: dict):
        self.atr_period      = params["atr_period"]
        self.vol_multiplier  = params["vol_multiplier"]
        self.volat_threshold = params["volat_threshold"]
        self.high_lookback   = params["high_lookback"]

    def generate_long(self, df: pd.DataFrame) -> pd.Series:
        # breakout, volume, volatility 필터
        breakout      = df['close'] > (df['close'].shift(1) + df['atr'])
        volume_ok     = df['volume'] > df['vol_ma'] * self.vol_multiplier
        volatility_ok = df['atr'] > (df['close'] * self.volat_threshold)
        return breakout & volume_ok & volatility_ok

    def generate_short(self, df: pd.DataFrame) -> pd.Series:
        breakout_short = df['close'] < (df['close'].shift(1) - df['atr'])
        volume_ok      = df['volume'] > df['vol_ma'] * self.vol_multiplier
        volatility_ok  = df['atr'] > (df['close'] * self.volat_threshold)
        return breakout_short & volume_ok & volatility_ok

# ===== /home/stongone123/freqtrade/src/utils/entry_signal.py 끝 =====

# ===== /home/stongone123/freqtrade/src/utils/exit_signal.py 시작 =====
# modules/exit_signal.py

import pandas as pd
from pandas import DataFrame, Series

class ExitSignal:
    def __init__(self, params: dict):
        # 필요시 파라미터 초기화
        pass

    def generate_long(self, df: DataFrame) -> Series:
        """
        Alligator lips가 teeth 아래로 교차할 때만
        롱 청산 시그널(True) 반환 (Python bool)
        """
        cond = df['lips'] < df['teeth']
        prev = df['lips'].shift(1) >= df['teeth'].shift(1)
        signal = (cond & prev).fillna(False)

        # Python bool 리스트로 변환
        py_list = [bool(val) for val in signal.tolist()]
        # object dtype Series로 만들어 Python bool 유지
        return pd.Series(py_list, index=signal.index, dtype=object)

    def generate_short(self, df: DataFrame) -> Series:
        """
        Alligator lips가 teeth 위로 교차할 때만
        숏 청산 시그널(True) 반환 (Python bool)
        """
        cond = df['lips'] > df['teeth']
        prev = df['lips'].shift(1) <= df['teeth'].shift(1)
        signal = (cond & prev).fillna(False)

        py_list = [bool(val) for val in signal.tolist()]
        return pd.Series(py_list, index=signal.index, dtype=object)

# ===== /home/stongone123/freqtrade/src/utils/exit_signal.py 끝 =====

# ===== /home/stongone123/freqtrade/src/utils/__init__.py 시작 =====

# ===== /home/stongone123/freqtrade/src/utils/__init__.py 끝 =====

# ===== /home/stongone123/freqtrade/src/utils/logger.py 시작 =====
# src/utils/logger.py
import logging
def setup_logger(name: str):
    """구조화된 JSON 로거 설정 반환"""
    pass

# ===== /home/stongone123/freqtrade/src/utils/logger.py 끝 =====

# ===== /home/stongone123/freqtrade/src/utils/helpers.py 시작 =====
# src/utils/helpers.py
def deep_merge_dicts(a: dict, b: dict) -> dict:
    """두 딕셔너리 병합(재귀)"""
    pass

# ===== /home/stongone123/freqtrade/src/utils/helpers.py 끝 =====

# ===== /home/stongone123/freqtrade/src/utils/secrets.py 시작 =====
# src/utils/secrets.py
import os
class SecretLoader:
    def get(self, key: str) -> str:
        """환경변수 또는 Vault에서 시크릿 가져오기"""
        pass

# ===== /home/stongone123/freqtrade/src/utils/secrets.py 끝 =====

# ===== /home/stongone123/freqtrade/src/utils/config_history.py 시작 =====
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

# ===== /home/stongone123/freqtrade/src/utils/config_history.py 끝 =====

# ===== /home/stongone123/freqtrade/src/utils/config.py 시작 =====
import json
import jsonschema
from pydantic import BaseModel, ValidationError
from typing import Optional, List, Dict
from src.utils.config_history import add_settings_history

class RiskManagement(BaseModel):
    max_drawdown: Optional[float]
    value_at_risk: Optional[float]

class Settings(BaseModel):
    entry_signals: List[str]
    short_signals: List[str]
    exit_signals: Optional[List[str]]
    signal_threshold: float
    signal_weights: Dict[str, float]
    api_keys: Optional[Dict[str, str]]
    min_signal_count: int
    env: str
    feature_flags: Optional[Dict[str, bool]]
    risk_management: Optional[RiskManagement]
    backtest: Optional[Dict]
    alerts: Optional[Dict]
    dashboard: Optional[Dict]
    slippage: Optional[float]
    fee: Optional[float]

def load_config(config_path="config/config_dev.json", schema_path="schemas/config_schema.json"):
    with open(config_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if schema_path:
        with open(schema_path, "r", encoding="utf-8") as sf:
            schema = json.load(sf)
        jsonschema.validate(instance=raw, schema=schema)
    try:
        settings = Settings(**raw)
        add_settings_history(config_path)
        return settings
    except ValidationError as e:
        print("⚠️ ValidationError!\n", e)
        raise
# ===== /home/stongone123/freqtrade/src/utils/config.py 끝 =====

# ===== /home/stongone123/freqtrade/src/utils/common.py 시작 =====
import time
import logging

logger = logging.getLogger(__name__)

def fetch_with_retry(request_fn, max_retries=3, backoff_base=1, timeout=5, fallback=None):
    for attempt in range(1, max_retries + 1):
        try:
            return request_fn(timeout=timeout)
        except Exception as e:
            logger.warning(f"[재시도] {attempt}회 실패: {e}")
            if attempt < max_retries:
                sleep_sec = backoff_base * (2 ** (attempt - 1))
                time.sleep(sleep_sec)
            else:
                logger.error(f"[최종실패] {max_retries}회 실패: {e}")
                if fallback is not None:
                    logger.warning("[대체값 반환] Fallback 값 사용")
                    return fallback
                else:
                    raise

# ===== /home/stongone123/freqtrade/src/utils/common.py 끝 =====

