# tests/test_strategy_mode.py

import pytest
from hybrid_alligator_atr_relaxed import HybridAlligatorATRRelaxedStrategy

@pytest.mark.parametrize(
    "mode, expected_can_long, expected_can_short",
    [
        ("spot",    True, False),
        ("futures", True, True),
        ("FoReCaSt", True, False),  # 소문자 변환 확인
    ]
)
def test_trading_mode_flag(mode, expected_can_long, expected_can_short):
    # 최소한 trading_mode 키만 있으면 __init__이 동작하도록 테스트
    config = {"trading_mode": mode}
    strat = HybridAlligatorATRRelaxedStrategy(config)
    assert strat.can_long  is expected_can_long
    assert strat.can_short is expected_can_short
