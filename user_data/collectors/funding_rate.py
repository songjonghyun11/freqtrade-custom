# funding_rate.py
import os, json, time
from typing import Dict, Any

class FundingRateCollector:
    def __init__(self, mode='realtime', data_dir='data'):
        self.mode = mode
        self.data_dir = data_dir
        self._cache: Dict[str, Dict[int, Dict[str, Any]]] = {}

    def _load_jsonl(self, symbol: str, name: str) -> Dict[int, Dict[str, Any]]:
        key = f"{symbol}:{name}"
        if key in self._cache:
            return self._cache[key]
        path = os.path.join(self.data_dir, symbol, f"{name}.json")
        data: Dict[int, Dict[str, Any]] = {}
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    it = json.loads(line)
                    ts = int(it.get("timestamp"))
                    # 표준 키로 정규화
                    fr = float(it.get("funding_rate", it.get("rate", 0.0)))
                    data[ts] = {"symbol": symbol, "funding_rate": fr, "timestamp": ts}
        self._cache[key] = data
        return data

    def fetch(self, symbol: str, timestamp: int = None):
        if self.mode == 'realtime':
            return {
                "symbol": symbol,
                "funding_rate": 0.01,         # 키 표준화
                "timestamp": int(time.time())  # epoch int 통일
            }
        # backtest
        if timestamp is None:
            raise ValueError("backtest 모드에선 timestamp(int, epoch) 필요")
        data = self._load_jsonl(symbol, "funding_rate")
        # 정확매칭 없으면 직전값 사용(FFILL) — look-ahead 방지
        keys = sorted(data.keys())
        prev = max([k for k in keys if k <= timestamp], default=None)
        return data.get(prev, {"symbol": symbol, "funding_rate": 0.0, "timestamp": timestamp})
