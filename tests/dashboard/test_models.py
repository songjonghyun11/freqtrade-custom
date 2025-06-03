from src.dashboard.models import Trade, Reflection

def test_trade_model():
    t = Trade(id=1, symbol="BTCUSDT", price=41000, qty=0.01)
    assert t.symbol == "BTCUSDT"

def test_reflection_model():
    r = Reflection(id=1, content="테스트", timestamp="2024-01-01T00:00:00")
    assert r.content == "테스트"
