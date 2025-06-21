import pytest
from src.collectors.fear_greed import fetch_fear_greed
from src.collectors.orderbook import fetch_orderbook

symbols = ["ETH", "SOL", "XRP", "ADA", "AVAX", "MATIC", "LINK", "LTC"]

@pytest.mark.parametrize("symbol", symbols)
def test_fetch_fear_greed(symbol):
    result = fetch_fear_greed(symbol)
    assert isinstance(result, dict), "결과가 dict가 아님"
    assert "value" in result and result["value"] is not None
    assert "value_classification" in result
    assert "timestamp" in result

@pytest.mark.parametrize("symbol", symbols)
def test_fetch_orderbook(symbol):
    result = fetch_orderbook(symbol)
    assert isinstance(result, list), f"실전 fetch_orderbook 결과는 list여야 함, 현재: {type(result)}"
    assert all(isinstance(item, dict) for item in result), "리스트 안에 dict 항목이 있어야 함"
    
    for order in result:
        assert "asks" in order and isinstance(order["asks"], list), "'asks' 필드가 없거나 리스트가 아님"
        assert "bids" in order and isinstance(order["bids"], list), "'bids' 필드가 없거나 리스트가 아님"
        assert "symbol" in order and isinstance(order["symbol"], str), "'symbol' 필드 누락 또는 타입 오류"
        assert "timestamp" in order and isinstance(order["timestamp"], int), "'timestamp' 필드 누락 또는 타입 오류"
