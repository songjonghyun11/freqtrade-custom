import talib
from ..interfaces import IEntrySignal
from ..signal import Signal, Direction

class RSIMomentumSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        close = ctx[symbol]['close']

        rsi_period = params[symbol].get('rsi_period', 14)
        rsi_low = params[symbol].get('rsi_low', 35)
        rsi_high = params[symbol].get('rsi_high', 55)

        rsi = talib.RSI(close, timeperiod=rsi_period)[-1]

        if rsi_low < rsi < rsi_high:
            score = 1.0
        else:
            score = 0.0

        return Signal("rsi_momentum", Direction.LONG, score)
