from freqtrade.strategy import IStrategy
from freqtrade.strategy.parameters import RealParameter, IntParameter
import talib.abstract as ta
import numpy as np
import pandas as pd
from pandas import DataFrame
from interfaces import IEntrySignal, IExitSignal, IRiskManager, IShortSignal

from entry_signals.alligator_atr import AlligatorATRSignal
from entry_signals.ema_crossover import EMACrossoverSignal
from entry_signals.rsi_momentum import RSIMomentumSignal
from entry_signals.vw_macd import VWMacdSignal

from exit_signals.trailing_stop_exit import TrailingStopExit
from exit_signals.ema_cross_exit import EMACrossExit

from risk.dynamic_stoploss import DynamicStoploss




class HybridAlligatorATRRelaxedStrategy(IStrategy):
    # Freqtrade 필수 기본 설정
    timeframe = '5m'
    startup_candle_count = 50

    # 파라미터 (하이퍼옵트 대상)
    sl_atr_multiplier = RealParameter(0.5, 3.0, default=1.5, space='sell', optimize=True, load=True)
    stoploss = -0.23
    stoploss_param = RealParameter(-0.10, -0.01, default=-0.02441, space='sell', optimize=True, load=True)

    minimal_roi = {
        "0":   0.245,
        "26":  0.048,
        "50":  0.021,
        "121": 0
    }

    trailing_stop = True
    trailing_stop_positive = 0.03
    trailing_stop_positive_offset = 0.05
    trailing_only_offset_is_reached = False

    process_only_new_candles = True
    use_custom_stoploss = True

    atr_period      = IntParameter(8, 21,  default=14,  space='buy', optimize=True, load=True)
    vol_multiplier  = RealParameter(1.0, 3.0, default=1.2,  space='buy', optimize=True, load=True)
    volat_threshold = RealParameter(0.003,0.02, default=0.005, space='buy', optimize=True, load=True)
    high_lookback   = IntParameter(1, 7,   default=3,    space='buy', optimize=True, load=True)

    def __init__(self, config: dict) -> None:
        super().__init__(config)
        # 전략별 신호 리스트화 (신호별 파라미터는 각 신호에서 처리 or 전달)
        self.entry_signals = [
            AlligatorATRSignal(),
            # EMACrossoverSignal(),
            # RSIMomentumSignal(),
            # VWMacdSignal(),
            # ... 필요하면 추가
        ]
        self.exit_signals = [
            # TrailingStopExit(),
             EMACrossExit(),
            # ... 필요하면 추가
        ]
        self.risk_modules = [
             DynamicStoploss(),
            # ... 필요하면 추가
        ]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Alligator + 각종 지표 예시 (진입 신호 모듈에서 추가 지표 쓸 수도 있음)
        hl2 = (dataframe['high'] + dataframe['low']) / 2
        dataframe['jaw']   = pd.Series(ta.EMA(hl2, timeperiod=13), index=dataframe.index).shift(8)
        dataframe['teeth'] = pd.Series(ta.EMA(hl2, timeperiod=8),  index=dataframe.index).shift(5)
        dataframe['lips']  = pd.Series(ta.EMA(hl2, timeperiod=5),  index=dataframe.index).shift(3)
        dataframe['adx']     = ta.ADX(dataframe, timeperiod=14)
        dataframe['plusdi']  = ta.PLUS_DI(dataframe, timeperiod=14)
        dataframe['minusdi'] = ta.MINUS_DI(dataframe, timeperiod=14)
        dataframe['atr']    = ta.ATR(dataframe, timeperiod=self.atr_period.value)
        dataframe['vol_ma'] = dataframe['volume'].rolling(10).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 여러 신호 OR/AND 조합 - 예: 하나라도 True면 진입(OR), 다 True여야 진입(AND)
        # 각 신호 generate 함수가 pd.Series(bool) 반환해야 정상 작동
        entry_results = [sig.generate(dataframe, metadata['pair'], {}) for sig in self.entry_signals]
        dataframe['enter_long'] = np.logical_or.reduce(entry_results)  # OR 조합, AND 조합이면 logical_and로!
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        exit_results = [sig.generate(dataframe, metadata['pair'], {}) for sig in self.exit_signals]
        dataframe['exit_long'] = np.logical_or.reduce(exit_results)
        return dataframe

    def custom_stoploss(self, pair: str, trade, current_time, current_rate, current_profit, **kwargs) -> float:
        df = self.dp.get_pair_dataframe(pair)
        period = int(self.atr_period.value)
        atr_series = ta.ATR(df, timeperiod=period)
        atr = atr_series.iloc[-1]
        # 여러 risk 모듈을 쓸 경우, 가장 보수적인(최소) 손절로 설정 가능
        stoploss_prices = [risk.adjust_stoploss(trade, trade.open_rate, {"atr": atr}) for risk in self.risk_modules]
        stoploss_price = min(stoploss_prices)
        return stoploss_price / trade.open_rate - 1
