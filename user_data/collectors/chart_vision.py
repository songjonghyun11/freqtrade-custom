# chart_vision.py
import os, json, time
from typing import Dict, Any, Optional
from datetime import datetime, timezone

def _parse_ts(raw) -> Optional[int]:
    """
    ISO 문자열("2025-01-01T09:00:00" / "2025-01-01T09:00:00Z") 또는
    epoch(int/str) 모두 안전하게 epoch(int)로 변환.
    """
    if raw is None:
        return None
    # 이미 숫자면
    if isinstance(raw, (int, float)):
        return int(raw)
    # 문자열이면
    if isinstance(raw, str):
        s = raw.strip()
        # "1704067200" 같은 숫자 문자열
        if s.isdigit():
            return int(s)
        # ISO 형식
        try:
            s2 = s.replace("Z", "")  # "Z" 제거
            dt = datetime.fromisoformat(s2)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except Exception:
            return None
    return None

class ChartVisionCollector:
    def __init__(self, mode='realtime', data_dir='data'):
        self.mode = mode
        self.data_dir = data_dir
        self._cache: Dict[str, Dict[int, Dict[str, Any]]] = {}

    def _load_jsonl(self, symbol: str) -> Dict[int, Dict[str, Any]]:
        if symbol in self._cache:
            return self._cache[symbol]

        path = os.path.join(self.data_dir, symbol, "chart_vision.json")
        series: Dict[int, Dict[str, Any]] = {}

        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    it = json.loads(line)

                    # nested("data": { "timestamp": ... }) 또는 flat("timestamp": ...)
                    raw_ts = (it.get("data") or {}).get("timestamp", it.get("timestamp"))
                    ts = _parse_ts(raw_ts)
                    if ts is None:
                        # 파싱 불가 레코드는 스킵
                        continue

                    chart_desc = (it.get("data") or {}).get("chart", it.get("chart", "dummy"))
                    series[ts] = {"chart": chart_desc, "timestamp": ts}

        self._cache[symbol] = series
        return series

    def fetch(self, symbol: str, timestamp: int = None, chart_path: str = None):
        if self.mode == 'realtime':
            return {"chart": f"{symbol}_realtime_chart", "timestamp": int(time.time())}
        if timestamp is None:
            raise ValueError("backtest 모드에는 timestamp(int epoch) 필요")

        data = self._load_jsonl(symbol)
        if not data:
            return {"chart": None, "timestamp": int(timestamp)}

        keys = sorted(data.keys())
        tgt = max([k for k in keys if k <= int(timestamp)], default=None)  # ffill
        return data.get(tgt, {"chart": None, "timestamp": int(timestamp)})
