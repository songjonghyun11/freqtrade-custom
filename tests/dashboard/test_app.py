from fastapi.testclient import TestClient
from src.dashboard.app import app

client = TestClient(app)

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

def test_get_trades_empty():
    resp = client.get("/trades")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

def test_get_reflections_empty():
    resp = client.get("/reflections")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
