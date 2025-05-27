from src.collectors.funding_rate import fetch_funding_rate

def test_fetch_funding_rate_exists():
    """fetch_funding_rate 함수가 정의되어 있어야 합니다."""
    assert callable(fetch_funding_rate)
