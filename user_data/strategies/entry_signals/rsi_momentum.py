import talib
from interfaces import IEntrySignal

class RSIMomentumSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        close = ctx['close']
        rsi_period = params.get('rsi_period', 14)          # ← 파라미터 기본값(14)
        rsi_threshold = params.get('rsi_threshold', 50)    # ← 파라미터 기본값(50)
        rsi = talib.RSI(close, timeperiod=rsi_period)
        cond = (rsi > rsi_threshold) & (rsi > rsi.shift(1)) & (close > close.shift(1))

        return cond.fillna(False)