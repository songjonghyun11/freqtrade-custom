# tests/test_bootstrap.py

from bootstrap import bootstrap
from src.strategies.strategy_orchestrator import StrategyOrchestrator

def test_bootstrap_flow():
    agg = bootstrap(
        config_path="tests/config_entry_signals.json",
        db_url="sqlite:///:memory:"
    )
    assert isinstance(agg, StrategyOrchestrator)
    # 기본 short_signals가 빈 리스트라 False
    assert agg.decide_short({}) is False
    # long 결정 메서드가 존재하는지
    assert hasattr(agg, "decide_long")
