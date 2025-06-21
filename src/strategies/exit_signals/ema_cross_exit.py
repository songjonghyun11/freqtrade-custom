import talib
from ..interfaces import IExitSignal
from ..signal import Signal, Direction

class EMACrossExitSignal(IExitSignal):
    def generate(self, ctx, symbol, params, position=None):
        close = ctx[symbol]['close']
        # 심볼별 파라미터 (없으면 디폴트)
        fast_period = params[symbol].get('exit_fast_ema', 9)
        slow_period = params[symbol].get('exit_slow_ema', 21)

        fast_ema = talib.EMA(close, timeperiod=fast_period)[-1]
        slow_ema = talib.EMA(close, timeperiod=slow_period)[-1]

        if fast_ema < slow_ema:
            score = 1.0
        else:
            score = 0.0

        return Signal("ema_cross_exit", Direction.EXIT, score)
