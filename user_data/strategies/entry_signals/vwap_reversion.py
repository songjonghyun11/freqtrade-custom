import pandas as pd
import talib.abstract as ta
from interfaces import IEntrySignal

class VWAPReversionSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        df = ctx
        vwap_period = params.get("vwap_period", 20)
        threshold = params.get("threshold", 0.985)

        vwap = (df["close"][-vwap_period:] * df["volume"][-vwap_period:]).sum() / df["volume"][-vwap_period:].sum()
        cond = df["close"] < vwap * threshold
        return cond.fillna(False)
