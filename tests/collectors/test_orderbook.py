from src.collectors.orderbook import fetch_orderbook

def test_fetch_orderbook_exists():
    """fetch_orderbook 함수가 정의되어 있어야 합니다."""
    assert callable(fetch_orderbook)
