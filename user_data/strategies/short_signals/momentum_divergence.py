import talib
from interfaces import IShortSignal
from mysignal import Signal, Direction

class MomentumDivergenceSignal(IShortSignal):
    def generate(self, ctx, symbol, params):
        close = ctx[symbol]['close']
        macd_cfg = params[symbol].get('macd', {"fast":12, "slow":26, "signal":9})
        macd, macdsignal, _ = talib.MACD(
            close,
            fastperiod=macd_cfg['fast'],
            slowperiod=macd_cfg['slow'],
            signalperiod=macd_cfg['signal'],
        )
        div_period = params[symbol].get('div_period', 10)
        if close[-1] > max(close[-div_period:-1]) and macd[-1] < macd[-2]:
            score = 1.0
        else:
            score = 0.0
        return Signal("momentum_divergence", Direction.SHORT, score)
