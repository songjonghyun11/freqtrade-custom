from src.collectors.fear_greed import fetch_fear_greed

def test_fetch_fear_greed_exists():
    """fetch_fear_greed 함수가 정의되어 있어야 합니다."""
    assert callable(fetch_fear_greed)
