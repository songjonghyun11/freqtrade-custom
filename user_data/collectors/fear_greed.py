import os, json
from datetime import datetime

class FearGreedCollector:
    def __init__(self, mode='realtime', data_dir='data'):
        self.mode = mode
        self.data_dir = data_dir
        self._cache = {}  # { "BTC_USDT:fear_greed": {ts: item, ...} }

    def _load_jsonl(self, symbol: str, name: str):
        key = f"{symbol}:{name}"
        if key in self._cache:
            return self._cache[key]
        path = os.path.join(self.data_dir, symbol, f"{name}.json")
        data = {}
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    it = json.loads(line)
                    ts = int(it.get("timestamp"))
                    # 표준화
                    val = float(it.get("value", 50))
                    cls = it.get("value_classification", "Neutral")
                    data[ts] = {"value": val, "value_classification": cls, "timestamp": ts}
        self._cache[key] = data
        return data

    def fetch(self, symbol: str, timestamp=None):
        if self.mode == 'realtime':
            return {"value": 50, "value_classification": "Neutral", "timestamp": int(datetime.now().timestamp())}
        if timestamp is None:
            raise ValueError("백테스트에서는 timestamp(int) 필요")
        data = self._load_jsonl(symbol, "fear_greed")
        if not data:
            return {"value": 50, "value_classification": "Neutral", "timestamp": int(timestamp)}
        keys = sorted(data.keys())
        prev = max([k for k in keys if k <= int(timestamp)], default=None)
        return data.get(prev, {"value": 50, "value_classification": "Neutral", "timestamp": int(timestamp)})
