import pandas as pd
import numpy as np
from interfaces import IEntrySignal

class SupertrendSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        df = ctx["data"].copy()
        atr_period = params.get("atr_period", 10)
        atr_multiplier = params.get("atr_multiplier", 3.0)

        hl2 = (df["high"] + df["low"]) / 2
        atr = df["high"].rolling(atr_period).max() - df["low"].rolling(atr_period).min()
        atr = atr.fillna(method='backfill')  # NaN 방어

        upper_band = hl2 + (atr_multiplier * atr)
        lower_band = hl2 - (atr_multiplier * atr)

        in_uptrend = pd.Series(index=df.index, data=True)

        for i in range(1, len(df)):
            if df["close"].iloc[i] > upper_band.iloc[i - 1]:
                in_uptrend.iloc[i] = True
            elif df["close"].iloc[i] < lower_band.iloc[i - 1]:
                in_uptrend.iloc[i] = False
            else:
                in_uptrend.iloc[i] = in_uptrend.iloc[i - 1]

        return in_uptrend.fillna(False)
