import pandas as pd
import talib.abstract as ta
from interfaces import IEntrySignal, Signal
from mysignal import Direction

class VWAPReversionSignal(IEntrySignal):
    def generate(self, ctx_or_df, symbol: str, params: dict) -> Signal:
        if isinstance(ctx_or_df, pd.DataFrame):
            df = ctx_or_df
            ctx = {symbol: {"ohlcv": df}}
        else:
            ctx = ctx_or_df
            df = ctx[symbol]["ohlcv"]

        vwap_period = params.get("vwap_period", 20)
        threshold = params.get("threshold", 0.985)

        vwap = (df["close"][-vwap_period:] * df["volume"][-vwap_period:]).sum() / df["volume"][-vwap_period:].sum()
        cond = df["close"] < vwap * threshold

        indexes = list(df.index[cond.fillna(False)])

        return Signal(
            name="vwap_reversion",
            indexes=indexes,
            direction=Direction.LONG,
            score=1.0,
            meta={
                "vwap_period": vwap_period,
                "threshold": threshold,
                "vwap": float(vwap),
            }
        )
