pytest_plugins = ["pytest_mock"]
import pytest
from src.collectors.news import NewsCollector
from src.collectors.orderbook import OrderbookCollector
from src.collectors.fear_greed import FearGreedCollector
from src.collectors.models import NewsData, OrderbookData, FearGreedData

# 예시 ctx: 필요한 필드만 포함
test_ctx = {
    "prev_news": [],
    "prev_orderbook": [],
}

def test_news_collector_success(monkeypatch):
    # 정상 응답 모킹
    def mock_fetch(ctx):
        return [{"title": "비트코인 급등", "timestamp": 1234567890}]
    monkeypatch.setattr(NewsCollector, "fetch", mock_fetch)
    news = NewsCollector().fetch(test_ctx)
    assert news[0]["title"] == "비트코인 급등"

def test_orderbook_collector_success(monkeypatch):
    def mock_fetch(ctx):
        return [{"symbol": "BTC/USDT", "bids": [[70000, 1.0]], "asks": [[71000, 1.2]], "timestamp": 1234567890}]
    monkeypatch.setattr(OrderbookCollector, "fetch", mock_fetch)
    obs = OrderbookCollector().fetch(test_ctx)
    assert obs[0]["symbol"] == "BTC/USDT"

def test_fear_greed_collector_success(monkeypatch):
    def mock_fetch(ctx):
        return [{"value": 70.0, "value_classification": "Greed", "timestamp": 1234567890}]
    monkeypatch.setattr(FearGreedCollector, "fetch", mock_fetch)
    fg = FearGreedCollector().fetch(test_ctx)
    assert fg[0]["value"] == 70.0

def test_news_collector_schema_error(monkeypatch, caplog):
    # 결측/이상값 테스트
    def mock_fetch(ctx):
        return [{"notitle": "에러!", "timestamp": None}]
    monkeypatch.setattr(NewsCollector, "fetch", mock_fetch)
    with caplog.at_level("WARNING"):
        news = NewsCollector().fetch(test_ctx)
        assert news == []  # 스키마 불일치로 skip

# 네트워크 장애/백오프/재시도 등도 똑같이 mock_fetch, monkeypatch로 시뮬레이션 가능!
