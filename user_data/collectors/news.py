# news.py (핵심)
import os, json
from typing import List, Dict

class NewsCollector:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir

    def fetch_news(self, symbol: str, timestamp: int = None) -> List[Dict]:
        path = os.path.join(self.data_dir, symbol, "news.json")
        out: List[Dict] = []
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    it = json.loads(line)
                    ts = int(it.get("timestamp", 0))
                    if (timestamp is None) or (ts <= int(timestamp)):
                        out.append({"title": it.get("title",""), "content": it.get("content",""), "timestamp": ts, "url": it.get("url")})
        return sorted(out, key=lambda x: x["timestamp"])
