from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy.parameters import IntParameter
from pandas import DataFrame
from exit_signals.ema_cross_exit import EMACrossExit

class TestEMACrossExitSignalStrategy(IStrategy):
    minimal_roi = {"0": 0.1}
    stoploss = -0.3
    timeframe = '5m'
    startup_candle_count = 30

    exit_fast_ema = IntParameter(5, 15, default=9, space="sell")
    exit_slow_ema = IntParameter(15, 30, default=21, space="sell")

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.exit_signal = EMACrossExit()

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        fast = self.exit_fast_ema.value
        slow = self.exit_slow_ema.value
        signal = self.exit_signal.generate(dataframe, metadata["pair"], {
            "exit_fast_ema": fast,
            "exit_slow_ema": slow,
        })
        dataframe["exit_long"] = 0
        if hasattr(signal, "indexes") and signal.indexes:
            dataframe.loc[signal.indexes, "exit_long"] = 1
        return dataframe
