# tests/collectors/social_media.py (테스트 전용)
from datetime import datetime
from .quality_guard import check_missing, check_duplicates

def fetch_social_media(symbol):
    # 테스트용 더미 데이터 (심볼별로 리스트 반환)
    dummy = [{
        "keyword": f"{symbol}_test_trend",
        "score": 77,
        "timestamp": datetime.utcnow().isoformat()
    }]
    # 필드 체크 (테스트용, 항상 통과하게 설계)
    if not check_missing(dummy[0], ["keyword", "score", "timestamp"], symbol=symbol):
        return []
    return dummy

def fetch_social_media(symbol):
    # 테스트 기준: 리스트 안에 dict(각각에 "platform", "keyword", "score", "timestamp" 등)가 있어야 함
    return [
    {
        "platform": "twitter",
        "keyword": f"{symbol}_test_trend",
        "score": 77,
        "content": "이 코인은 대세!",   # <-- content 추가!
        "timestamp": "2025-01-01"
    }
]