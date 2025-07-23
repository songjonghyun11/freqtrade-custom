from freqtrade.strategy.interface import IStrategy
from freqtrade.strategy.parameters import RealParameter
from pandas import DataFrame
from exit_signals.roi_target_exit import ROITargetExitSignal

class TestROITargetExitSignalStrategy(IStrategy):
    minimal_roi = {"0": 0.1}
    stoploss = -0.3
    timeframe = '5m'
    startup_candle_count = 30

    roi_target = RealParameter(0.01, 0.15, default=0.04, space="sell")

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.exit_signal = ROITargetExitSignal()

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # entry_price, current_price 없으면 테스트용으로 생성
        if "entry_price" not in dataframe.columns:
            dataframe["entry_price"] = dataframe["close"].shift(1)
        if "current_price" not in dataframe.columns:
            dataframe["current_price"] = dataframe["close"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["enter_long"] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        roi = self.roi_target.value
        signal = self.exit_signal.generate(dataframe, metadata["pair"], {"roi_target": roi})
        dataframe["exit_long"] = 0
        if hasattr(signal, "indexes") and signal.indexes:
            dataframe.loc[signal.indexes, "exit_long"] = 1
        return dataframe
