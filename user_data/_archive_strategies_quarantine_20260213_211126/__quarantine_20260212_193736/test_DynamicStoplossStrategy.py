from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy.parameters import RealParameter
from pandas import DataFrame
from strategies.risk.dynamic_stoploss import DynamicStoploss

class TestDynamicStoplossStrategy(IStrategy):
    minimal_roi = {"0": 0.1}
    stoploss = -0.3
    timeframe = '5m'
    startup_candle_count = 30

    profit_threshold = RealParameter(0.01, 0.1, default=0.03, space="sell")
    stop_threshold = RealParameter(-0.15, -0.01, default=-0.05, space="sell")
    profit_sl = RealParameter(0.95, 1.0, default=0.98, space="sell")
    loss_sl = RealParameter(0.90, 1.0, default=0.97, space="sell")

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.risk = DynamicStoploss(
            profit_threshold=self.profit_threshold.value,
            stop_threshold=self.stop_threshold.value,
            profit_sl=self.profit_sl.value,
            loss_sl=self.loss_sl.value
        )

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        return self.risk.adjust_stoploss(pair, trade, current_time, current_rate, current_profit, **kwargs)
