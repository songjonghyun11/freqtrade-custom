import pandas as pd
import talib.abstract as ta
from interfaces import IEntrySignal

class VWAPReversionSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        df = ctx["data"]

        vwap_period = 20
        vwap = (df["close"][-vwap_period:] * df["volume"][-vwap_period:]).sum() / df["volume"][-vwap_period:].sum()

        cond = df["close"] < vwap * 0.985

        return cond.fillna(False)
