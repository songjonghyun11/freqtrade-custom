# tests/persistence/test_database_manager.py

import pytest
from src.persistence.database_manager import DatabaseManager

@pytest.fixture
def dm():
    # 메모리 DB로 인스턴스 생성
    return DatabaseManager(db_url="sqlite:///:memory:")

def test_methods_exist(dm):
    """
    get_recent_trades, get_reflection_history, add_reflection, record_trade
    네 가지 메서드가 모두 존재하고 호출 가능한지 검증합니다.
    """
    assert callable(getattr(dm, "get_recent_trades", None)), "get_recent_trades 메서드가 없습니다"
    assert callable(getattr(dm, "get_reflection_history", None)), "get_reflection_history 메서드가 없습니다"
    assert callable(getattr(dm, "add_reflection", None)), "add_reflection 메서드가 없습니다"
    assert callable(getattr(dm, "record_trade", None)), "record_trade 메서드가 없습니다"
