from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy.parameters import RealParameter
from pandas import DataFrame
from entry_signals.donchian import DonchianBreakoutSignal

class TestDonchianSignalStrategy(IStrategy):
    minimal_roi = {"0": 0.1}
    stoploss = -0.3
    timeframe = '5m'
    startup_candle_count = 20

    buy_breakout_threshold = RealParameter(0.97, 1.03, default=1.0, space="buy")

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.signal = DonchianBreakoutSignal()

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        threshold = self.buy_breakout_threshold.value
        signal = self.signal.generate(dataframe, metadata["pair"], {"threshold": threshold})
        dataframe["enter_long"] = 0
        if hasattr(signal, "indexes") and signal.indexes:
            dataframe.loc[signal.indexes, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        return dataframe
