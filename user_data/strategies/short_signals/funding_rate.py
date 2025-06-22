from interfaces import IShortSignal
from mysignal import Signal, Direction

class FundingRateSignal(IShortSignal):
    def generate(self, ctx, symbol, params):
        funding = ctx[symbol]['funding']
        threshold = params[symbol].get('funding_threshold', 0.0005)
        if funding > threshold:
            score = 1.0
        else:
            score = 0.0
        return Signal("funding_rate", Direction.SHORT, score)
