import pandas as pd
import talib.abstract as ta
from interfaces import IEntrySignal

class VWMacdSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        df = ctx["data"]

        macd, macdsignal, _ = ta.MACD(df["close"], fastperiod=12, slowperiod=26, signalperiod=9)
        vwap_period = 20
        vwap = (df["close"][-vwap_period:] * df["volume"][-vwap_period:]).sum() / df["volume"][-vwap_period:].sum()

        cond = (
            (macd > macdsignal) &
            (df["close"] > vwap)
        )

        return cond.fillna(False)
