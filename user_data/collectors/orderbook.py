import os, json, time
from datetime import datetime
from typing import Dict, Any, List

def _imbalance(bids: List[List[str]], asks: List[List[str]]) -> float:
    b = sum(float(q) for _, q in bids[:10]) if bids else 0.0
    a = sum(float(q) for _, q in asks[:10]) if asks else 0.0
    denom = b + a
    return (b - a) / denom if denom > 0 else 0.0

class OrderbookCollector:
    def __init__(self, mode='backtest', data_dir='data'):
        self.mode = mode
        self.data_dir = data_dir
        self._cache: Dict[str, Dict[int, Dict[str, Any]]] = {}

    def _load_jsonl(self, symbol):
        if symbol in self._cache: return self._cache[symbol]
        path = os.path.join(self.data_dir, symbol, "orderbook.json")
        data = {}
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    it = json.loads(line)
                    ts = int(it.get("timestamp"))
                    bids = it.get("bids", [])
                    asks = it.get("asks", [])
                    data[ts] = {
                        "symbol": symbol,
                        "bids": bids,
                        "asks": asks,
                        "timestamp": ts,
                        "imbalance": _imbalance(bids, asks)
                    }
        self._cache[symbol] = data
        return data

    def fetch(self, symbol: str, timestamp: int = None):
        if self.mode == 'realtime':
            return {"symbol": symbol, "bids": [], "asks": [], "timestamp": int(time.time()), "imbalance": 0.0}
        if timestamp is None: raise ValueError("backtest는 timestamp 필요")
        data = self._load_jsonl(symbol)
        keys = sorted(data.keys())
        prev = max([k for k in keys if k <= timestamp], default=None)
        return data.get(prev, {"symbol": symbol, "bids": [], "asks": [], "timestamp": timestamp, "imbalance": 0.0})