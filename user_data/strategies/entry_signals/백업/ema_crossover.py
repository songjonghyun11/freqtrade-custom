import talib
from interfaces import IEntrySignal

class EMACrossoverSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        close = ctx['close'] 

        ema_fast = talib.EMA(close, timeperiod=12)
        ema_slow = talib.EMA(close, timeperiod=26)

        crossover = (ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1))
        return crossover.fillna(False)
