import pandas as pd
import talib.abstract as ta
from interfaces import IEntrySignal, Signal
from mysignal import Direction

class VWMacdSignal(IEntrySignal):
    def generate(self, ctx_or_df, symbol: str, params: dict) -> Signal:
        if isinstance(ctx_or_df, pd.DataFrame):
            df = ctx_or_df
            ctx = {symbol: {"ohlcv": df}}
        else:
            ctx = ctx_or_df
            df = ctx[symbol]["ohlcv"]

        fastperiod = params.get("fastperiod", 12)
        slowperiod = params.get("slowperiod", 26)
        signalperiod = params.get("signalperiod", 9)
        vwap_period = params.get("vwap_period", 20)

        macd, macdsignal, _ = ta.MACD(df["close"], fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
        # VWAP 계산 (최근 vwap_period 구간)
        vwap = (df["close"][-vwap_period:] * df["volume"][-vwap_period:]).sum() / df["volume"][-vwap_period:].sum()

        cond = (macd > macdsignal) & (df["close"] > vwap)
        indexes = list(df.index[cond.fillna(False)])

        return Signal(
            name="vw_macd",
            indexes=indexes,
            direction=Direction.LONG,
            score=1.0,
            meta={
                "fastperiod": fastperiod,
                "slowperiod": slowperiod,
                "signalperiod": signalperiod,
                "vwap_period": vwap_period,
                "vwap": float(vwap)
            }
        )
