import os
import json

class NewsCollector:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir

    def fetch_news(self, symbol: str, timestamp=None):
        # 백테스트용: 과거 시점별 뉴스 데이터 파일에서 로드
        file_path = os.path.join(self.data_dir, symbol, "news.json")
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"{file_path} 파일 없음")
        news_list = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                item = json.loads(line)
                # timestamp가 없으면 전체 반환, 있으면 해당 시점 뉴스만 반환
                if timestamp is None or int(item.get("timestamp", 0)) == int(timestamp):
                    news_list.append(item)
        return news_list  # 리스트로 반환
