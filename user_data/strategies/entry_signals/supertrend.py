import pandas as pd
import numpy as np
from interfaces import IEntrySignal, Signal
from mysignal import Direction

class SupertrendSignal(IEntrySignal):
    def generate(self, ctx_or_df, symbol: str, params: dict) -> Signal:
        if isinstance(ctx_or_df, pd.DataFrame):
            df = ctx_or_df
            ctx = {symbol: {"ohlcv": df}}
        else:
            ctx = ctx_or_df
            df = ctx[symbol]["ohlcv"]

        atr_period = params.get("atr_period", 10)
        atr_multiplier = params.get("atr_multiplier", 3.0)

        hl2 = (df["high"] + df["low"]) / 2
        atr = df["high"].rolling(atr_period).max() - df["low"].rolling(atr_period).min()
        atr = atr.bfill()  # NaN 방어

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

        # 진입 인덱스만 추출
        indexes = list(df.index[in_uptrend.fillna(False)])

        return Signal(
            name="supertrend",
            indexes=indexes,
            direction=Direction.LONG,
            score=1.0,
            meta={
                "atr_period": atr_period,
                "atr_multiplier": atr_multiplier,
            }
        )
