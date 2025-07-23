import pandas as pd
from interfaces import IEntrySignal, Signal
from mysignal import Direction

class DonchianBreakoutSignal(IEntrySignal):
    weight = 1.0

    def generate(self, ctx_or_df, symbol: str, params: dict) -> Signal:
        if isinstance(ctx_or_df, pd.DataFrame):
            df = ctx_or_df
            ctx = {symbol: {"ohlcv": df}}
        else:
            ctx = ctx_or_df
            df = ctx[symbol]["ohlcv"]

        high = df["high"].rolling(20).max()
        close = df["close"]

        threshold = params.get("threshold", 1.0)
        breakout = close.iloc[-1] > high.iloc[-2] * threshold
        score = 1.0 if breakout else 0.0

        indexes = [df.index[-1]] if breakout else []

        return Signal(
            name="donchian",
            indexes=indexes,
            direction=Direction.LONG,
            score=score,
            confidence=0.85,
            meta={
                "breakout_level": round(high.iloc[-2], 2),
                "price": round(close.iloc[-1], 2),
                "threshold": threshold,
            }
        )
