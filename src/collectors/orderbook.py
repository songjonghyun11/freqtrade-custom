import os
import json
from datetime import datetime

class OrderbookCollector:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir

    def fetch(self, symbol: str, timestamp=None):
        """
        백테스트 모드: 시점별 오더북 데이터를 파일에서 읽어옴
        파일명 예시: data/BTC_USDT/orderbook.json (한 줄당 1개 스냅샷)
        """
        file_path = os.path.join(self.data_dir, symbol, "orderbook.json")
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"{file_path} 파일 없음")
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                item = json.loads(line)
                if timestamp is None or int(item.get("timestamp", 0)) == int(timestamp):
                    return item
        # 해당 시점 데이터 없으면 더미 반환
        return {
            "symbol": symbol,
            "bids": [["100.0", "1.0"]],
            "asks": [["101.0", "1.5"]],
            "timestamp": int(timestamp or datetime.now().timestamp())
        }
