import talib
import numpy as np
from ..interfaces import IEntrySignal
from ..signal import Signal, Direction

class VWMacdSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        close = ctx[symbol]['close']
        volume = ctx[symbol].get('volume', np.ones_like(close))

        macd_cfg = params[symbol].get('macd', {"fast":12, "slow":26, "signal":9})
        vwap_period = params[symbol].get('vwap_period', 20)

        macd, macdsignal, _ = talib.MACD(
            close,
            fastperiod=macd_cfg['fast'],
            slowperiod=macd_cfg['slow'],
            signalperiod=macd_cfg['signal'],
        )
        vwap = np.sum(close[-vwap_period:] * volume[-vwap_period:]) / np.sum(volume[-vwap_period:])

        if macd[-1] > macdsignal[-1] and close[-1] > vwap:
            score = 1.0
        else:
            score = 0.0

        return Signal("vw_macd", Direction.LONG, score)
