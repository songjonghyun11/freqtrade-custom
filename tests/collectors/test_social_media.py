# tests/collectors/test_social_media.py

from src.collectors.social_media import fetch_trends

def test_fetch_trends_exists():
    """fetch_trends 함수가 정의되어 있어야 합니다."""
    assert callable(fetch_trends)
