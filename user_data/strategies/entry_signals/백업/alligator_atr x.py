from interfaces import IEntrySignal, Signal
from mysignal import Direction
import pandas as pd
import talib.abstract as ta
from pandas import DataFrame
from typing import Optional

class AlligatorATRSignal(IEntrySignal):
    def generate(self, df: DataFrame, symbol: str, params) -> Signal:
        if isinstance(params, dict):
            ema_jaw = params.get('ema_jaw', 13)
            ema_teeth = params.get('ema_teeth', 8)
            ema_lips = params.get('ema_lips', 5)
            atr_period = params.get('atr_period', 14)
        else:
            ema_jaw = 13
            ema_teeth = 8
            ema_lips = 5
            atr_period = 14

        hl2 = (df["high"] + df["low"]) / 2
        jaw = pd.Series(ta.EMA(hl2, timeperiod=ema_jaw), index=df.index).shift(8)
        teeth = pd.Series(ta.EMA(hl2, timeperiod=ema_teeth), index=df.index).shift(5)
        lips = pd.Series(ta.EMA(hl2, timeperiod=ema_lips), index=df.index).shift(3)
        atr = ta.ATR(df, timeperiod=atr_period)

        entry = (
            (lips > teeth) &
            (teeth > jaw) &
            (df['close'] > lips) &
            (atr > 0)
        )

        return Signal(
            name="alligator_atr",
            indexes=entry[entry].index,
            direction=Direction.LONG,
            meta={
                'atr': atr.iloc[-1],
                'jaw': jaw.iloc[-1],
                'teeth': teeth.iloc[-1],
                'lips': lips.iloc[-1],
                'close': df['close'].iloc[-1]
            }
        )
