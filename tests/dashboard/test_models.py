from src.dashboard.models import Trade, Reflection
from datetime import datetime

def test_trade_model():
    t = Trade(id=1, timestamp=datetime.utcnow(), data={})
    assert t.id == 1
    assert isinstance(t.timestamp, datetime)

def test_reflection_model():
    r = Reflection(timestamp=datetime.utcnow(), data={})
    assert r.id is None or isinstance(r.id, int)
