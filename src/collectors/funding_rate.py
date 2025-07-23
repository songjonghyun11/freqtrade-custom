import os
import json
from datetime import datetime

class FundingRateCollector:
    def __init__(self, mode='realtime', data_dir='data'):
        self.mode = mode
        self.data_dir = data_dir

    def fetch(self, symbol: str, timestamp=None):
        if self.mode == 'realtime':
            # (실전) 기존 fetch 코드(실시간 API 호출/로깅 등) 그대로 사용
            # 여기선 예시로 더미값만 반환
            return {
                "symbol": symbol,
                "rate": 0.01,
                "timestamp": datetime.utcnow().isoformat()
            }
        elif self.mode == 'backtest':
            # (백테스트) data/BTC_USDT/funding_rate.json (여러 줄, 한 줄씩 파싱)
            if timestamp is None:
                raise ValueError("백테스트에서는 timestamp를 반드시 전달해야 합니다!")
            file_path = os.path.join(self.data_dir, symbol, "funding_rate.json")
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"{file_path} 파일 없음")
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    item = json.loads(line)
                    if str(item.get("timestamp")) == str(timestamp):
                        return item
            # 해당 시점 데이터 없으면 더미값 반환
            return {
                "symbol": symbol,
                "rate": 0.01,
                "timestamp": timestamp
            }
        else:
            raise ValueError("mode는 realtime 또는 backtest만 지원")
