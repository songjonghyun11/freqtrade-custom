from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy.parameters import IntParameter
from pandas import DataFrame
from entry_signals.rsi_momentum import RSIMomentumSignal

class TestRSIMomentumSignalStrategy(IStrategy):
    minimal_roi = {"0": 0.1}
    stoploss = -0.3
    timeframe = '5m'
    startup_candle_count = 30

    # 하이퍼옵트용 파라미터
    rsi_period = IntParameter(8, 30, default=14, space="buy")
    rsi_threshold = IntParameter(45, 70, default=50, space="buy")

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.signal = RSIMomentumSignal()

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        period = self.rsi_period.value
        threshold = self.rsi_threshold.value
        signal = self.signal.generate(dataframe, metadata["pair"], {"rsi_period": period, "rsi_threshold": threshold})
        dataframe["enter_long"] = 0
        if hasattr(signal, "indexes") and signal.indexes:
            dataframe.loc[signal.indexes, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        return dataframe
