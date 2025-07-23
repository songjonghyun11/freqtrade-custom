# import numpy as np
# import pandas as pd
# from pandas import DataFrame

# import talib.abstract as ta
# from freqtrade.strategy import IStrategy
# from freqtrade.strategy.parameters import RealParameter, IntParameter, DecimalParameter
# from freqtrade.strategy import IntParameter

# from entry_signals.rsi_momentum import RSIMomentumSignal
# from entry_signals.supertrend import SupertrendSignal
# from entry_signals.ema_crossover import EMACrossoverSignal
# from entry_signals.alligator_atr import AlligatorATRSignal
# from entry_signals.donchian import DonchianBreakoutSignal
# from entry_signals.trend_volume import TrendVolumeSignal
# from entry_signals.vw_macd import VWMacdSignal
# from entry_signals.vwap_reversion import VWAPReversionSignal

# from exit_signals.ema_cross_exit import EMACrossExit
# from exit_signals.exit_to_neutral import ExitToNeutralSignal
# from exit_signals.roi_target_exit import ROITargetExitSignal
# from exit_signals.trailing_stop_exit import TrailingStopExitSignal

# from risk.dynamic_stoploss import DynamicStoploss
# from risk.portfolio_mdd import PortfolioMDDRisk
  
# class HybridAlligatorATRRelaxedStrategy(IStrategy):
#     INTERFACE_VERSION = 3

#     timeframe = '5m'
#     can_short = False
#     process_only_new_candles = True
#     startup_candle_count = 50

#     use_custom_stoploss = True
#     use_exit_signal = True
#     ignore_roi_if_entry_signal = False

#     # ▼ 글로벌 파라미터
#     minimal_roi = {
#         "0": 0.171,
#         "10": 0.047,
#         "60": 0.021,
#         "180": 0
#     }
#     stoploss = -0.334

#     #리스크 신호용 하이퍼옵트 파라미터 선언
#     profit_threshold = RealParameter(0.01, 0.10, default=0.03, space="sell")
#     stop_threshold = RealParameter(-0.15, -0.01, default=-0.05, space="sell")
#     profit_sl = RealParameter(0.95, 1.0, default=0.95911, space="sell")
#     loss_sl = RealParameter(0.92, 1.0, default=0.92526, space="sell")


#     # 청산 신호용 하이퍼옵트 파라미터 선언
#     exit_fast_ema = IntParameter(5, 30, default=16, space="sell")         # 19
#     exit_slow_ema = IntParameter(10, 60, default=51, space="sell")        # 49
#     neutral_threshold = RealParameter(0.1, 0.8, default=0.29107, space="sell") # 0.48513
#     roi_target = RealParameter(0.02, 0.1, default=0.05461, space="sell")
#     sl_atr_multiplier = RealParameter(1.0, 3.5, default=1.76973, space="sell")  # 2.61203      
#     trail_perc = RealParameter(0.01, 0.05, default=0.02512, space="sell")     # 1~5%, 디폴트 2%



#     # 진입 신호용 파라미터
#     atr_period = IntParameter(7, 21, default=9, space="buy")                    #  9
#     donchian_period = IntParameter(10, 50, default=40, space="buy")              # 40
#     ema_fast_period = IntParameter(7, 50, default=16, space="buy")               # 16
#     ema_slow_period = IntParameter(20, 120, default=21, space="buy")            # 107
#     high_lookback = IntParameter(2, 8, default=6, space="buy")                   # 4
#     rsi_period = IntParameter(8, 20, default=10, space="buy")                    # 14
#     rsi_threshold = IntParameter(40, 70, default=58, space="buy")                # 40
#     supertrend_atr_multiplier = RealParameter(1.0, 6.0, default=1.57829, space="buy") # 1.91887
#     supertrend_atr_period = IntParameter(7, 40, default=29, space="buy")         # 10
#     trend_ema_fast_period = IntParameter(7, 30, default=24, space="buy")         # 26
#     trend_ema_slow_period = IntParameter(20, 100, default=62, space="buy")       # 28  
#     trend_vol_ma_period = IntParameter(10, 60, default=14, space="buy")          # 32
#     vol_multiplier = RealParameter(0.5, 4.0, default=3.36912, space="buy")       # 1.84844
#     volat_threshold = RealParameter(0.001, 0.05, default=0.04538, space="buy")   # 0.01361
#     vwaprev_period = IntParameter(10, 50, default=36, space="buy")               # 24
#     vwaprev_threshold = RealParameter(0.97, 1.0, default=0.99813, space="buy")    # 0.9966
#     vwmacd_fastperiod = IntParameter(7, 20, default=12, space="buy")              # 7
#     vwmacd_signalperiod = IntParameter(5, 30, default=9, space="buy")           # 9
#     vwmacd_slowperiod = IntParameter(20, 50, default=23, space="buy")            # 35
#     vwmacd_vwap_period = IntParameter(10, 40, default=22, space="buy")           # 24

#     def __init__(self, config: dict) -> None:
#         super().__init__(config)
#         self.entry_signals = [
#         AlligatorATRSignal(),
#         DonchianBreakoutSignal(),
#         EMACrossoverSignal(),
#         SupertrendSignal(),
#         RSIMomentumSignal(),
#         TrendVolumeSignal(),
#         VWMacdSignal(),
#         VWAPReversionSignal()
#         ]
#         self.exit_signals = [
#         EMACrossExit(),
#         ExitToNeutralSignal(),
#         ROITargetExitSignal(),
#         TrailingStopExitSignal()]

#     def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
#         hl2 = (dataframe["high"] + dataframe["low"]) / 2
#         dataframe['jaw'] = pd.Series(ta.EMA(hl2, timeperiod=13), index=dataframe.index).shift(8)
#         dataframe['teeth'] = pd.Series(ta.EMA(hl2, timeperiod=8), index=dataframe.index).shift(5)
#         dataframe['lips'] = pd.Series(ta.EMA(hl2, timeperiod=5), index=dataframe.index).shift(3)
#         return dataframe

#     def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
#         pair = metadata['pair']
#         param_sets = [
#         {   # AlligatorATRSignal
#             'atr_period': self.atr_period.value,
#             'high_lookback': self.high_lookback.value,
#             'volat_threshold': self.volat_threshold.value,
#             'vol_multiplier': self.vol_multiplier.value
#         },
#         {   # DonchianBreakoutSignal
#             'donchian_period': self.donchian_period.value
#         },
#         {   # EMACrossoverSignal
#             'ema_fast_period': self.ema_fast_period.value,
#             'ema_slow_period': self.ema_slow_period.value
#         },
#         {   # SupertrendSignal (하이퍼옵스 연동)
#             'atr_period': self.supertrend_atr_period.value,
#             'atr_multiplier': self.supertrend_atr_multiplier.value
#         },
#         {   # SupertrendSignal (하이퍼옵스 연동)
#             'rsi_period': self.rsi_period.value,
#             'rsi_threshold': self.rsi_threshold.value
#         },
#         {   #trend_volumesignal
#         'ema_fast_period': self.trend_ema_fast_period.value,
#         'ema_slow_period': self.trend_ema_slow_period.value,
#         'vol_ma_period': self.trend_vol_ma_period.value
#         },
#         {   #VWMacdSignal
#         "fastperiod": self.vwmacd_fastperiod.value,
#         "slowperiod": self.vwmacd_slowperiod.value,
#         "signalperiod": self.vwmacd_signalperiod.value,
#         "vwap_period": self.vwmacd_vwap_period.value
#         },
#         {   #VWAPReversionSignal
#         "vwap_period": self.vwaprev_period.value,
#         "threshold": self.vwaprev_threshold.value
#         }
#     ]
#         for i, sig in enumerate(self.entry_signals):
#             entry_cond = sig.generate(dataframe, pair, param_sets[i])
#             dataframe.loc[entry_cond, 'enter_long'] = 1
#         return dataframe

#     def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
#         param_sets = [{
#             # EMACrossExit
#             'exit_fast_ema': self.exit_fast_ema.value,
#             'exit_slow_ema': self.exit_slow_ema.value},  
#         {'neutral_threshold': self.neutral_threshold.value}, # ExitToNeutralSignal
#         {'roi_target': self.roi_target.value},# ROITargetExitSignal
#         {'trail_perc': self.trail_perc.value}# TrailingStopExitSignal
#         ]
        
#         for i, sig in enumerate(self.exit_signals):
#             exit_cond = sig.generate(dataframe, metadata['pair'], param_sets[i])
#             dataframe.loc[exit_cond, 'exit_long'] = 1
#         return dataframe

#     # 전략 클래스 내부
#     def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
#         # 안전하게 파라미터 접근!
#         mdd_limit_obj = getattr(self, "mdd_limit", None)
#         if mdd_limit_obj is not None:
#             mdd_limit_val = mdd_limit_obj.value
#         else:
#             mdd_limit_val = 0.10  # fallback 디폴트
     
#         risk_modules = [
#             DynamicStoploss(
#                 profit_threshold=getattr(self, "profit_threshold", type("dummy", (), {"value": 0.03})()).value,
#                 stop_threshold=getattr(self, "stop_threshold", type("dummy", (), {"value": -0.05})()).value,
#                 profit_sl=getattr(self, "profit_sl", type("dummy", (), {"value": 0.98})()).value,
#                 loss_sl=getattr(self, "loss_sl", type("dummy", (), {"value": 0.97})()).value,
#                 ),
#             PortfolioMDDRisk(
#                mdd_limit=mdd_limit_val
#             )
#         ]
#         for risk_module in risk_modules:
#             stop = risk_module.adjust_stoploss(pair, trade, current_time, current_rate, current_profit, **kwargs)
#             if stop is not None and stop != trade.stop_loss:
#                 return stop
#         return trade.stop_loss


#     def _get_signal_param_sets(self, signals):
#         if hasattr(self, 'ft_params') and isinstance(self.ft_params, dict):
#             return [
#                 {k: v for k, v in self.ft_params.items()
#                  if k.startswith(sig.__class__.__name__[:6].lower())}
#                 for sig in signals
#             ]
#         return [{} for _ in signals]
