import pytest
import json
from src.persistence.database_manager import DatabaseManager

@pytest.fixture
def dm(tmp_path):
    db_file = tmp_path / "test.db"
    url = f"sqlite:///{db_file}"
    return DatabaseManager(db_url=url)

def test_record_and_fetch_trade(dm):
    tid = dm.record_trade({"price":100, "qty":1})
    assert isinstance(tid, int)
    rows = dm.get_recent_trades(10)
    assert len(rows) == 1
    assert json.loads(rows[0][2]) == {"price":100, "qty":1}

def test_add_and_fetch_reflection(dm):
    rid = dm.add_reflection({"note":"test"})
    assert isinstance(rid, int)
    rows = dm.get_reflection_history(5)
    assert len(rows) == 1
    assert json.loads(rows[0][2]) == {"note":"test"}
