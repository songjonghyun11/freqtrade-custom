from modules.risk_manager import RiskManager

def test_calculate_stoploss():
    rm = RiskManager(2.0)
    assert rm.calculate_stoploss(100, 5) == 100 - 2*5

def test_should_abort():
    rm = RiskManager(1.0)
    assert rm.should_abort(0.5, max_dd=0.4) is True
    assert rm.should_abort(0.3, max_dd=0.4) is False
