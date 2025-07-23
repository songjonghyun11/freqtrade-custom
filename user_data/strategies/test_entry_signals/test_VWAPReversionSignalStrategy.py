from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy.parameters import IntParameter, RealParameter
from pandas import DataFrame
from entry_signals.vwap_reversion import VWAPReversionSignal

class TestVWAPReversionSignalStrategy(IStrategy):
    minimal_roi = {"0": 0.1}
    stoploss = -0.3
    timeframe = '5m'
    startup_candle_count = 30

    vwap_period = IntParameter(10, 40, default=20, space="buy")
    threshold = RealParameter(0.97, 1.01, default=0.985, space="buy")

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.signal = VWAPReversionSignal()

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        period = self.vwap_period.value
        th = self.threshold.value
        signal = self.signal.generate(dataframe, metadata["pair"], {
            "vwap_period": period,
            "threshold": th
        })
        dataframe["enter_long"] = 0
        if hasattr(signal, "indexes") and signal.indexes:
            dataframe.loc[signal.indexes, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        return dataframe
