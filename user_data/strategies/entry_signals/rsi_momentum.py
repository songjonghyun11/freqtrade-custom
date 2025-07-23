import pandas as pd
import talib
from interfaces import IEntrySignal, Signal
from mysignal import Direction

class RSIMomentumSignal(IEntrySignal):
    def generate(self, ctx_or_df, symbol: str, params: dict) -> Signal:
        if isinstance(ctx_or_df, pd.DataFrame):
            df = ctx_or_df
            ctx = {symbol: {"ohlcv": df}}
        else:
            ctx = ctx_or_df
            df = ctx[symbol]["ohlcv"]

        close = df["close"]

        rsi_period = params.get('rsi_period', 14)
        rsi_threshold = params.get('rsi_threshold', 50)
        rsi = talib.RSI(close, timeperiod=rsi_period)
        cond = (rsi > rsi_threshold) & (rsi > rsi.shift(1)) & (close > close.shift(1))

        indexes = df.index[cond.fillna(False)]

        return Signal(
            name="rsi_momentum",
            indexes=list(indexes),
            direction=Direction.LONG,
            score=1.0,
            meta={
                "rsi_period": rsi_period,
                "rsi_threshold": rsi_threshold,
            }
        )
