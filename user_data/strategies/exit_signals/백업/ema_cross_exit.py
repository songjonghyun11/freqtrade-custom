import talib.abstract as ta
from interfaces import IExitSignal
from mysignal import Signal, Direction
from pandas import DataFrame

class EMACrossExit(IExitSignal):
    def generate(self, ctx, symbol, params, position=None):
        df = ctx  # ✅ Freqtrade에서는 ctx = DataFrame

        # Hyperopt에서 넘어온 값 처리
        fast = params.get('exit_fast_ema', 9)
        slow = params.get('exit_slow_ema', 21)
        fast = fast.value if hasattr(fast, 'value') else fast
        slow = slow.value if hasattr(slow, 'value') else slow

        fast_ema = ta.EMA(df["close"], timeperiod=fast)
        slow_ema = ta.EMA(df["close"], timeperiod=slow)

        score = 1.0 if fast_ema[-1] < slow_ema[-1] else 0.0
        return Signal("ema_cross_exit", Direction.EXIT, score)
