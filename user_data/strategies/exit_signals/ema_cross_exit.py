import talib
from interfaces import IExitSignal
from mysignal import Signal, Direction

class EMACrossExit(IExitSignal):  # ✅ 클래스 이름을 EMACrossExit로 변경
    def generate(self, ctx, symbol, params, position=None):
        df = ctx  # ✅ Freqtrade에서는 ctx = DataFrame

        fast_period = params.get('exit_fast_ema', 9)
        slow_period = params.get('exit_slow_ema', 21)

        fast_ema = talib.EMA(df["close"], timeperiod=fast_period)
        slow_ema = talib.EMA(df["close"], timeperiod=slow_period)

        score = 1.0 if fast_ema.iloc[-1] < slow_ema.iloc[-1] else 0.0
        return Signal("ema_cross_exit", Direction.EXIT, score)
