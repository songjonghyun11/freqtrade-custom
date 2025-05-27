from src.collectors.news import fetch_news

def test_fetch_news_exists():
    """fetch_news 함수가 정의되어 있어야 합니다."""
    assert callable(fetch_news)
