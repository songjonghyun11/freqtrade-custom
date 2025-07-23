from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy.parameters import IntParameter
from pandas import DataFrame
from entry_signals.trend_volume import TrendVolumeSignal

class TestTrendVolumeSignalStrategy(IStrategy):
    minimal_roi = {"0": 0.1}
    stoploss = -0.3
    timeframe = '5m'
    startup_candle_count = 30

    ema_fast_period = IntParameter(7, 20, default=12, space="buy")
    ema_slow_period = IntParameter(14, 30, default=26, space="buy")
    vol_ma_period = IntParameter(10, 40, default=20, space="buy")

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.signal = TrendVolumeSignal()

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        fast = self.ema_fast_period.value
        slow = self.ema_slow_period.value
        vol_ma = self.vol_ma_period.value
        signal = self.signal.generate(dataframe, metadata["pair"], {
            "ema_fast_period": fast,
            "ema_slow_period": slow,
            "vol_ma_period": vol_ma
        })
        dataframe["enter_long"] = 0
        if hasattr(signal, "indexes") and signal.indexes:
            dataframe.loc[signal.indexes, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        return dataframe
