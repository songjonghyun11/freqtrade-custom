import pandas as pd
import talib.abstract as ta
from interfaces import IExitSignal, Signal
from mysignal import Direction

class EMACrossExit(IExitSignal):
    def generate(self, ctx_or_df, symbol: str, params: dict, position=None) -> Signal:
        if isinstance(ctx_or_df, pd.DataFrame):
            df = ctx_or_df
        else:
            df = ctx_or_df[symbol]["ohlcv"]

        fast = params.get('exit_fast_ema', 9)
        slow = params.get('exit_slow_ema', 21)
        # Hyperopt 객체일 때 .value로 변환
        fast = fast.value if hasattr(fast, 'value') else fast
        slow = slow.value if hasattr(slow, 'value') else slow

        fast_ema = pd.Series(ta.EMA(df["close"], timeperiod=fast))
        slow_ema = pd.Series(ta.EMA(df["close"], timeperiod=slow))

        exit_cross = (fast_ema < slow_ema) & (fast_ema.shift(1) >= slow_ema.shift(1))
        indexes = list(df.index[exit_cross.fillna(False)])
        return Signal(
            name="ema_cross_exit",
            indexes=indexes,
            direction=Direction.EXIT,
            score=1.0,
            meta={
                "exit_fast_ema": fast,
                "exit_slow_ema": slow,
            }
        )
