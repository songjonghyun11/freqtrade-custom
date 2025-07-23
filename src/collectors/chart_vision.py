import os
import json
from datetime import datetime

class ChartVisionCollector:
    def __init__(self, mode='realtime', data_dir='data'):
        self.mode = mode
        self.data_dir = data_dir

    def fetch(self, symbol, timestamp=None, chart_path=None):
        if self.mode == 'realtime':
            # (실전) API 호출 부분 생략, 기존 구현 사용
            # 실전에서는 chart_path를 API에 전달
            # ...
            return {
                "chart": {"type": f"{symbol}_realtime_chart"},
                "timestamp": datetime.utcnow().isoformat()
            }
        elif self.mode == 'backtest':
            # (백테스트) 과거 시점 데이터 로드
            if timestamp is None:
                raise ValueError("백테스트에서는 timestamp를 반드시 전달해야 합니다!")
            # 파일명: data/BTC_USDT/chart_vision.json (여러줄, 한 줄씩 파싱)
            file_path = os.path.join(self.data_dir, symbol, "chart_vision.json")
            if not os.path.isfile(file_path):
                raise FileNotFoundError(f"{file_path} 파일 없음")
            # timestamp (iso 또는 int)로 매칭
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    item = json.loads(line)
                    if item["data"].get("timestamp") == timestamp:
                        return item["data"]
            # 없으면 더미 반환 (혹은 에러)
            return {"chart": None, "timestamp": timestamp}
        else:
            raise ValueError("mode는 realtime 또는 backtest만 지원")
