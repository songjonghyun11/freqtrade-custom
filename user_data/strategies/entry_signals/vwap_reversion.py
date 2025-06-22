import numpy as np
from interfaces import IEntrySignal
from signal import Signal, Direction

class VWAPReversionSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        close = ctx[symbol]['close']
        volume = ctx[symbol].get('volume', np.ones_like(close))
        vwap_period = params[symbol].get('vwap_period', 20)

        vwap = np.sum(close[-vwap_period:] * volume[-vwap_period:]) / np.sum(volume[-vwap_period:])

        if close[-1] > vwap:
            score = 1.0
        else:
            score = 0.0

        return Signal("vwap_reversion", Direction.LONG, score)
