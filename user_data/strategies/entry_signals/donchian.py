from interfaces import IEntrySignal
import pandas as pd
import talib.abstract as ta


class DonchianBreakoutSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        high = ctx['high']
        low = ctx['low']
        close = ctx['close']


        period = params.get('donchian_period', 20)

        upper = high.rolling(period).max().shift(1)  # 이전 캔들 기준
        breakout = close > upper

        return breakout.fillna(False)
