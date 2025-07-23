from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy.parameters import IntParameter, RealParameter
from pandas import DataFrame
from entry_signals.supertrend import SupertrendSignal

class TestSupertrendSignalStrategy(IStrategy):
    minimal_roi = {"0": 0.1}
    stoploss = -0.3
    timeframe = '5m'
    startup_candle_count = 30

    # 하이퍼옵트 파라미터 선언
    atr_period = IntParameter(7, 21, default=10, space="buy")
    atr_multiplier = RealParameter(2.0, 5.0, default=3.0, space="buy")

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.signal = SupertrendSignal()

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        period = self.atr_period.value
        multiplier = self.atr_multiplier.value
        signal = self.signal.generate(dataframe, metadata["pair"], {"atr_period": period, "atr_multiplier": multiplier})
        dataframe["enter_long"] = 0
        if hasattr(signal, "indexes") and signal.indexes:
            dataframe.loc[signal.indexes, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        return dataframe
