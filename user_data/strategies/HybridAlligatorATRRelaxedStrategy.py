import numpy as np
import pandas as pd
from pandas import DataFrame

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from freqtrade.strategy.parameters import RealParameter, IntParameter, DecimalParameter

from freqtrade.persistence import Trade
from entry_signals.alligator_atr import AlligatorATRSignal
from exit_signals.ema_cross_exit import EMACrossExit
from risk.dynamic_stoploss import DynamicStoploss

from datetime import datetime   
from typing import Optional    

class HybridAlligatorATRRelaxedStrategy(IStrategy):
    INTERFACE_VERSION = 3

    timeframe = '5m'
    can_short = False
    process_only_new_candles = True
    startup_candle_count = 50

    use_custom_stoploss = True
    use_exit_signal = True
    ignore_roi_if_entry_signal = False
    
    stoploss = -0.334  # (최적값)
    minimal_roi = {
        "0": 0.251,
        "33": 0.063,
        "46": 0.038,
        "125": 0
    }

    # 청산 신호용 하이퍼옵트 파라미터 선언
    exit_fast_ema = IntParameter(5, 20, default=12, space="sell")
    exit_slow_ema = IntParameter(10, 40, default=36, space="sell")

    atr_period = IntParameter(7, 21, default=20, space="buy")
    high_lookback = IntParameter(2, 5, default=4, space="buy")
    vol_multiplier = DecimalParameter(0.5, 3.0, default=0.671, space="buy")
    volat_threshold = DecimalParameter(0.001, 0.02, default=0.016, space="buy")

    sl_atr_multiplier = DecimalParameter(1.0, 2.5, default=1.329, space="sell")
    stoploss_param = DecimalParameter(-0.04, -0.01, default=-0.334, space="stoploss")

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.entry_signals = [AlligatorATRSignal()]
        self.exit_signals = [EMACrossExit()]
        self.risk_module = DynamicStoploss()

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        hl2 = (dataframe["high"] + dataframe["low"]) / 2
        dataframe['jaw'] = pd.Series(ta.EMA(hl2, timeperiod=13), index=dataframe.index).shift(8)
        dataframe['teeth'] = pd.Series(ta.EMA(hl2, timeperiod=8), index=dataframe.index).shift(5)
        dataframe['lips'] = pd.Series(ta.EMA(hl2, timeperiod=5), index=dataframe.index).shift(3)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        pair = metadata['pair']
        param_sets = [{
            'atr_period': self.atr_period.value,
            'high_lookback': self.high_lookback.value,
            'volat_threshold': self.volat_threshold.value,
            'vol_multiplier': self.vol_multiplier.value
        }]
        for i, sig in enumerate(self.entry_signals):
            entry_cond = sig.generate(dataframe, pair, param_sets[i])
            dataframe.loc[entry_cond, 'enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        param_sets = [{
            'exit_fast_ema': self.exit_fast_ema.value,
            'exit_slow_ema': self.exit_slow_ema.value
        }]
        for i, sig in enumerate(self.exit_signals):
            exit_cond = sig.generate(dataframe, metadata['pair'], param_sets[i])
            dataframe.loc[exit_cond, 'exit_long'] = 1
        return dataframe

    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime, current_rate: float,
                    current_profit: float, **kwargs) -> Optional[float]:
        return self.risk_module.adjust_stoploss(pair, trade, current_time, current_rate, current_profit, **kwargs)

    def _get_signal_param_sets(self, signals):
        if hasattr(self, 'ft_params') and isinstance(self.ft_params, dict):
            return [
                {k: v for k, v in self.ft_params.items()
                 if k.startswith(sig.__class__.__name__[:6].lower())}
                for sig in signals
            ]
        return [{} for _ in signals]
