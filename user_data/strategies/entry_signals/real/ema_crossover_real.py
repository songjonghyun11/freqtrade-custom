import talib
from interfaces import IEntrySignal
from mysignal import Signal, Direction

class EMACrossoverSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        close = ctx[symbol]['close']

        # 심볼별 파라미터 (없으면 디폴트)
        fast_period = params[symbol].get('fast_ema', 12)
        slow_period = params[symbol].get('slow_ema', 26)

        fast_ema = talib.EMA(close, timeperiod=fast_period)[-1]
        slow_ema = talib.EMA(close, timeperiod=slow_period)[-1]

        if fast_ema > slow_ema:
            score = 1.0
        else:
            score = 0.0

        return Signal("ema_crossover", Direction.LONG, score)
