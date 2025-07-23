import os
import json
from datetime import datetime

class FearGreedCollector:
    def __init__(self, mode='realtime', data_dir='data'):
        self.mode = mode
        self.data_dir = data_dir

    def fetch(self, symbol: str, timestamp=None):
        if self.mode == 'realtime':
            # (실전) 기존 fetch_with_retry, API 호출/파싱 코드 그대로 사용
            # 예시로 더미값만 반환
            return {
                "value": 50,
                "value_classification": "Neutral",
                "timestamp": int(datetime.now().timestamp())
            }
        elif self.mode == 'backtest':
            # (백테스트) 과거 시점별 공포탐욕 데이터를 파일에서 로드
            # data/BTC_USDT/fear_greed.json (여러 줄, 한 줄씩 파싱)
            if timestamp is None:
                raise ValueError("백테스트에서는 timestamp를 반드시 전달해야 합니다!")
            file_path = os.path.join(self.data_dir, symbol, "fear_greed.json")
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"{file_path} 파일 없음")
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    item = json.loads(line)
                    if int(item["timestamp"]) == int(timestamp):
                        return item
            # 해당 시점 데이터 없으면 더미 반환
            return {
                "value": 50,
                "value_classification": "Neutral",
                "timestamp": int(timestamp)
            }
        else:
            raise ValueError("mode는 realtime 또는 backtest만 지원")
