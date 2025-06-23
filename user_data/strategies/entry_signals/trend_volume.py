import pandas as pd
import talib.abstract as ta
from interfaces import IEntrySignal

class TrendVolumeSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        df = ctx["data"]

        # === 지표 계산 ===
        ema_fast = ta.EMA(df, timeperiod=12)
        ema_slow = ta.EMA(df, timeperiod=26)
        vol_ma = df["volume"].rolling(20).mean()

        # === 조건 ===
        cond = (
            (ema_fast > ema_slow) &
            (df["close"] > ema_fast) &
            (df["volume"] > vol_ma)
        )

        return cond.fillna(False)
