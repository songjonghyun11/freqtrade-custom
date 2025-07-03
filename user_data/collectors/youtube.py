# tests/collectors/youtube.py (테스트 전용)
from datetime import datetime
from collectors.quality_guard import check_missing

def fetch_youtube(symbol):
    # 테스트용 더미 데이터
    dummy = {
        "caption": f"{symbol}_youtube_caption_test",
        "timestamp": datetime.utcnow().isoformat()
    }
    if not check_missing(dummy, ["caption", "timestamp"], symbol=symbol):
        return {}
    return dummy

def fetch_youtube(symbol):
    # 테스트 기준: 리스트 안에 dict(각각에 "title", "url", "timestamp" 등)가 있어야 함
    return [
        {"title": f"{symbol}_youtube_title_test", "url": "https://youtube.com/test", "timestamp": "2025-01-01"}
    ]

class YouTubeCollector:
    def __init__(self):
        pass
    def fetch(self, symbol: str):
        return [
            {
                "symbol": symbol,
                "title": "예시 유튜브 영상",
                "views": 12345,
                "timestamp": int(datetime.now().timestamp())
            }
        ]
