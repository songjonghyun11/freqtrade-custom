import talib
from ..interfaces import IShortSignal
from ..signal import Signal, Direction

class RSIOverboughtSignal(IShortSignal):
    def generate(self, ctx, symbol, params):
        close = ctx[symbol]['close']
        rsi_period = params[symbol].get('rsi_period', 14)
        overbought = params[symbol].get('rsi_overbought', 70)
        rsi = talib.RSI(close, timeperiod=rsi_period)[-1]
        if rsi > overbought:
            score = 1.0
        else:
            score = 0.0
        return Signal("rsi_overbought", Direction.SHORT, score)
