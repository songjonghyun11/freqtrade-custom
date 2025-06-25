import pandas as pd
import talib.abstract as ta
from interfaces import IEntrySignal

class VWMacdSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        df = ctx
        fastperiod = params.get("fastperiod", 12)
        slowperiod = params.get("slowperiod", 26)
        signalperiod = params.get("signalperiod", 9)
        vwap_period = params.get("vwap_period", 20)

        macd, macdsignal, _ = ta.MACD(df["close"], fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
        vwap = (df["close"][-vwap_period:] * df["volume"][-vwap_period:]).sum() / df["volume"][-vwap_period:].sum()

        cond = (macd > macdsignal) & (df["close"] > vwap)
        return cond.fillna(False)
