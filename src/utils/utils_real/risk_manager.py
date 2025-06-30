# strategy/modules/risk_manager.py

class RiskManager:
    def __init__(self, stoploss_atr_multiplier: float):
        self.sl_multiplier = stoploss_atr_multiplier

    def calculate_stoploss(self, entry_price: float, atr: float) -> float:
        """
        동적 손절가 계산: entry_price - sl_multiplier * atr
        """
        return entry_price - self.sl_multiplier * atr

    def should_abort(self, portfolio_drawdown: float, max_dd: float) -> bool:
        """
        포트폴리오 MDD 기반 중단 여부
        """
        return portfolio_drawdown >= max_dd
