import numpy as np
import pandas as pd
from pandas import DataFrame

import talib.abstract as ta
from freqtrade.strategy import IStrategy
from freqtrade.strategy.parameters import RealParameter, IntParameter, DecimalParameter
from freqtrade.strategy import IntParameter

from freqtrade.persistence import Trade
from entry_signals.rsi_momentum import RSIMomentumSignal
from entry_signals.supertrend import SupertrendSignal
from entry_signals.ema_crossover import EMACrossoverSignal
from entry_signals.alligator_atr import AlligatorATRSignal
from entry_signals.donchian import DonchianBreakoutSignal
from entry_signals.trend_volume import TrendVolumeSignal
from entry_signals.vw_macd import VWMacdSignal
from entry_signals.vwap_reversion import VWAPReversionSignal
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

    # ▼ 글로벌 파라미터
    minimal_roi = {
        "0": 0.176,
        "34": 0.07,
        "86": 0.035,
        "175": 0
    }
    stoploss = -0.335

    # 청산 신호용 하이퍼옵트 파라미터 선언
    exit_fast_ema = IntParameter(5, 30, default=16, space="sell")         # 16
    exit_slow_ema = IntParameter(10, 50, default=18, space="sell")        # 18
    sl_atr_multiplier = RealParameter(1.0, 3.5, default=1.64535, space="sell")  # 1.64535


    # 진입 신호용 파라미터
    supertrend_atr_period = IntParameter(7, 30, default=21, space="buy")         # 21
    supertrend_atr_multiplier = RealParameter(1.0, 6.0, default=2.51422, space="buy") # 2.51422
    atr_period = IntParameter(7, 21, default=14, space="buy")                    # 14
    donchian_period = IntParameter(10, 40, default=21, space="buy")              # 21
    ema_fast_period = IntParameter(7, 50, default=17, space="buy")               # 17
    ema_slow_period = IntParameter(20, 120, default=107, space="buy")            # 107
    high_lookback = IntParameter(2, 6, default=5, space="buy")                   # 5
    vol_multiplier = RealParameter(0.5, 3.5, default=3.16864, space="buy")       # 3.16864
    volat_threshold = RealParameter(0.001, 0.05, default=0.03661, space="buy")   # 0.03661
    rsi_period = IntParameter(8, 20, default=18, space="buy")                    # 18
    rsi_threshold = IntParameter(40, 70, default=50, space="buy")                # 50
    trend_ema_fast_period = IntParameter(7, 30, default=17, space="buy")         # 17
    trend_ema_slow_period = IntParameter(20, 100, default=22, space="buy")       # 22
    trend_vol_ma_period = IntParameter(10, 60, default=50, space="buy")          # 50
    vwmacd_fastperiod = IntParameter(7, 20, default=18, space="buy")             # 18
    vwmacd_slowperiod = IntParameter(20, 50, default=24, space="buy")            # 24
    vwmacd_signalperiod = IntParameter(5, 30, default=6, space="buy")            # 6
    vwmacd_vwap_period = IntParameter(10, 40, default=27, space="buy")           # 27
    vwaprev_period = IntParameter(10, 50, default=23, space="buy")               # 23
    vwaprev_threshold = RealParameter(0.97, 1.0, default=0.97078, space="buy")   # 0.97078

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        self.entry_signals = [
        AlligatorATRSignal(),
        DonchianBreakoutSignal(),
        EMACrossoverSignal(),
        SupertrendSignal(),
        RSIMomentumSignal(),
        TrendVolumeSignal(),
        VWMacdSignal(),
        VWAPReversionSignal()
        ]
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
        param_sets = [
        {   # AlligatorATRSignal
            'atr_period': self.atr_period.value,
            'high_lookback': self.high_lookback.value,
            'volat_threshold': self.volat_threshold.value,
            'vol_multiplier': self.vol_multiplier.value
        },
        {   # DonchianBreakoutSignal
            'donchian_period': self.donchian_period.value
        },
        {   # EMACrossoverSignal
            'ema_fast_period': self.ema_fast_period.value,
            'ema_slow_period': self.ema_slow_period.value
        },
        {   # SupertrendSignal (하이퍼옵스 연동)
            'atr_period': self.supertrend_atr_period.value,
            'atr_multiplier': self.supertrend_atr_multiplier.value
        },
        {   # SupertrendSignal (하이퍼옵스 연동)
            'rsi_period': self.rsi_period.value,
            'rsi_threshold': self.rsi_threshold.value
        },
        {   #trend_volumesignal
        'ema_fast_period': self.trend_ema_fast_period.value,
        'ema_slow_period': self.trend_ema_slow_period.value,
        'vol_ma_period': self.trend_vol_ma_period.value
        },
        {   #VWMacdSignal
        "fastperiod": self.vwmacd_fastperiod.value,
        "slowperiod": self.vwmacd_slowperiod.value,
        "signalperiod": self.vwmacd_signalperiod.value,
        "vwap_period": self.vwmacd_vwap_period.value
        },
        {   #VWAPReversionSignal
        "vwap_period": self.vwaprev_period.value,
        "threshold": self.vwaprev_threshold.value
        }
    ]
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
