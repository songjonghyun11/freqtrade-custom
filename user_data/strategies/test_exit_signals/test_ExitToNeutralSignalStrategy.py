from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy.parameters import RealParameter
from pandas import DataFrame
from exit_signals.exit_to_neutral import ExitToNeutralSignal

class TestExitToNeutralSignalStrategy(IStrategy):
    minimal_roi = {"0": 0.1}
    stoploss = -0.3
    timeframe = '5m'
    startup_candle_count = 30

    neutral_threshold = RealParameter(0.1, 0.7, default=0.3, space="sell")

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.exit_signal = ExitToNeutralSignal()

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 테스트를 위해 aggregator_score 컬럼이 없으면 생성 (랜덤)
        if "aggregator_score" not in dataframe.columns:
            import numpy as np
            dataframe["aggregator_score"] = np.random.rand(len(dataframe))
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        threshold = self.neutral_threshold.value
        signal = self.exit_signal.generate(dataframe, metadata["pair"], {"neutral_threshold": threshold})
        dataframe["exit_long"] = 0
        if hasattr(signal, "indexes") and signal.indexes:
            dataframe.loc[signal.indexes, "exit_long"] = 1
        return dataframe
