from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy.parameters import IntParameter
from pandas import DataFrame
from entry_signals.vw_macd import VWMacdSignal

class TestVWMacdSignalStrategy(IStrategy):
    minimal_roi = {"0": 0.1}
    stoploss = -0.3
    timeframe = '5m'
    startup_candle_count = 30

    fastperiod = IntParameter(8, 20, default=12, space="buy")
    slowperiod = IntParameter(16, 32, default=26, space="buy")
    signalperiod = IntParameter(5, 15, default=9, space="buy")
    vwap_period = IntParameter(10, 40, default=20, space="buy")

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.signal = VWMacdSignal()

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        fast = self.fastperiod.value
        slow = self.slowperiod.value
        sig = self.signalperiod.value
        vwap_p = self.vwap_period.value
        signal = self.signal.generate(dataframe, metadata["pair"], {
            "fastperiod": fast,
            "slowperiod": slow,
            "signalperiod": sig,
            "vwap_period": vwap_p
        })
        dataframe["enter_long"] = 0
        if hasattr(signal, "indexes") and signal.indexes:
            dataframe.loc[signal.indexes, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        return dataframe
