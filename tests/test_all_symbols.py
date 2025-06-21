import pytest
from src.collectors.fear_greed import fetch_fear_greed
from src.collectors.orderbook import fetch_orderbook
from src.collectors.news import fetch_news  # (news.py 위치에 맞게 import)
from src.collectors.social_media import fetch_social_media
from src.collectors.youtube import fetch_youtube
from src.collectors.funding_rate import fetch_funding_rate
from src.collectors.chart_vision import fetch_chart_vision

symbols = ["ETH", "SOL", "XRP", "ADA", "AVAX", "MATIC", "LINK", "LTC"]

@pytest.mark.parametrize("symbol", symbols)
def test_fetch_chart_vision(symbol):
    result = fetch_chart_vision(symbol)
    assert isinstance(result, dict), "결과가 dict가 아님"
    assert "chart" in result and isinstance(result["chart"], dict)
    assert "timestamp" in result and isinstance(result["timestamp"], str)

@pytest.mark.parametrize("symbol", symbols)
def test_fetch_funding_rate(symbol):
    result = fetch_funding_rate(symbol)
    assert isinstance(result, dict), "결과가 dict가 아님"
    assert "symbol" in result and isinstance(result["symbol"], str)
    assert "rate" in result and isinstance(result["rate"], (float, int))
    assert "timestamp" in result and isinstance(result["timestamp"], str)

@pytest.mark.parametrize("symbol", symbols)
def test_fetch_youtube(symbol):
    result = fetch_youtube(symbol)
    assert isinstance(result, list)
    for video in result:
        assert "title" in video
        assert "url" in video
        assert "timestamp" in video

@pytest.mark.parametrize("symbol", symbols)
def test_fetch_social_media(symbol):
    result = fetch_social_media(symbol)
    assert isinstance(result, list)
    for post in result:
        assert "platform" in post
        assert "content" in post
        assert "timestamp" in post

@pytest.mark.parametrize("symbol", symbols)
def test_fetch_news(symbol):
    result = fetch_news(symbol)
    assert isinstance(result, list)
    for news in result:
        assert "title" in news
        assert "timestamp" in news
        assert "url" in news
        assert "source" in news
        assert "content" in news

@pytest.mark.parametrize("symbol", symbols)
def test_fetch_fear_greed(symbol):
    result = fetch_fear_greed(symbol)
    assert isinstance(result, dict)
    assert "value" in result and result["value"] is not None
    assert "value_classification" in result
    assert "timestamp" in result

@pytest.mark.parametrize("symbol", symbols)
def test_fetch_orderbook(symbol):
    result = fetch_orderbook(symbol)
    assert isinstance(result, list)
    for ob in result:
        assert isinstance(ob, dict)
        assert "symbol" in ob
        assert "bids" in ob
        assert "asks" in ob
        assert "timestamp" in ob
    
    for order in result:
        assert "asks" in order and isinstance(order["asks"], list), "'asks' 필드가 없거나 리스트가 아님"
        assert "bids" in order and isinstance(order["bids"], list), "'bids' 필드가 없거나 리스트가 아님"
        assert "symbol" in order and isinstance(order["symbol"], str), "'symbol' 필드 누락 또는 타입 오류"
        assert "timestamp" in order and isinstance(order["timestamp"], int), "'timestamp' 필드 누락 또는 타입 오류"
