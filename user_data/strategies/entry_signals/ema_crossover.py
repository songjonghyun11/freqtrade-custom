import pandas as pd
import talib
from interfaces import IEntrySignal, Signal
from mysignal import Direction

class EMACrossoverSignal(IEntrySignal):
    def generate(self, ctx_or_df, symbol: str, params: dict) -> Signal:
        if isinstance(ctx_or_df, pd.DataFrame):
            df = ctx_or_df
            ctx = {symbol: {"ohlcv": df}}
        else:
            ctx = ctx_or_df
            df = ctx[symbol]["ohlcv"]

        close = df['close']

        fast = params.get("fast", 12)
        slow = params.get("slow", 26)

        ema_fast = talib.EMA(close, timeperiod=fast)
        ema_slow = talib.EMA(close, timeperiod=slow)

        crossover = (ema_fast > ema_slow) & (ema_fast.shift(1) <= ema_slow.shift(1))
        indexes = df.index[crossover.fillna(False)]

        return Signal(
            name="ema_crossover",
            indexes=list(indexes),                # 리스트 형태로 반환!
            direction=Direction.LONG,
            score=1.0,
            meta={
                "ema_fast": fast,
                "ema_slow": slow,
            }
        )
