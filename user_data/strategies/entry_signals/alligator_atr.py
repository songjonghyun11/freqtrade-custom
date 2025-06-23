import numpy as np
import pandas as pd
import talib
from interfaces import IEntrySignal

class AlligatorATRSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        df = ctx  # ✅ 백테스트에서는 ctx 자체가 DataFrame

        ema_jaw = params.get('ema_jaw', 13)
        ema_teeth = params.get('ema_teeth', 8)
        ema_lips = params.get('ema_lips', 5)
        atr_period = params.get('atr_period', 14)
        atr_threshold = params.get('atr_threshold', 0.01)

        hl2 = (df["high"] + df["low"]) / 2

        jaw   = pd.Series(talib.EMA(hl2, timeperiod=ema_jaw), index=df.index).shift(8)
        teeth = pd.Series(talib.EMA(hl2, timeperiod=ema_teeth), index=df.index).shift(5)
        lips  = pd.Series(talib.EMA(hl2, timeperiod=ema_lips), index=df.index).shift(3)
        atr = talib.ATR(df["high"], df["low"], df["close"], timeperiod=atr_period)

        cond = (
        (lips > teeth) &
        (teeth > jaw) &
        (df["close"] > jaw) &
        (atr > atr_threshold)
        )

        return cond.fillna(False)