import talib
from interfaces import IEntrySignal

class RSIMomentumSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        close = ctx['data']['close']
        rsi = talib.RSI(close, timeperiod=14)

        # 조건: RSI가 50 초과 && 상승 중 && 종가도 상승 중
        cond = (rsi > 50) & (rsi > rsi.shift(1)) & (close > close.shift(1))

        return cond.fillna(False)
