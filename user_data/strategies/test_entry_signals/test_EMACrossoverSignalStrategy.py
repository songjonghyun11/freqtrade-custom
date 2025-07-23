from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy.parameters import IntParameter
from pandas import DataFrame
from entry_signals.ema_crossover import EMACrossoverSignal

class TestEMACrossoverSignalStrategy(IStrategy):
    minimal_roi = {"0": 0.1}
    stoploss = -0.3
    timeframe = '5m'
    startup_candle_count = 30

    # 하이퍼옵트용 파라미터 추가
    fast_ema = IntParameter(8, 20, default=12, space="buy")
    slow_ema = IntParameter(18, 40, default=26, space="buy")

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.signal = EMACrossoverSignal()

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        fast = self.fast_ema.value
        slow = self.slow_ema.value
        signal = self.signal.generate(dataframe, metadata["pair"], {"fast": fast, "slow": slow})
        dataframe["enter_long"] = 0
        if hasattr(signal, "indexes") and signal.indexes:
            dataframe.loc[signal.indexes, "enter_long"] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        return dataframe
