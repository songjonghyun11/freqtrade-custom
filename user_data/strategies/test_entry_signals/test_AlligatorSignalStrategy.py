import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy
from freqtrade.strategy.parameters import IntParameter, RealParameter

from entry_signals.alligator_atr import AlligatorATRSignal
from mysignal import Direction

class TestAlligatorSignalStrategy(IStrategy):
    minimal_roi = {"0": 0.1}
    stoploss = -0.2
    timeframe = '5m'

    alligator_atr_params = RealParameter(0.2, 3.0, default=1.0, space="buy")

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.entry_signals = [AlligatorATRSignal()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        if dataframe.empty:
            return dataframe

        signal = self.entry_signals[0].generate(
            dataframe,
            metadata["pair"],
            self.alligator_atr_params.value
        )

        if signal.direction == Direction.LONG:
            dataframe.loc[signal.indexes, 'enter_long'] = 1
        elif signal.direction == Direction.SHORT:
            dataframe.loc[signal.indexes, 'enter_short'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["exit_long"] = 0
        dataframe["exit_short"] = 0
        return dataframe
