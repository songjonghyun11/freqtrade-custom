import pandas as pd
import talib.abstract as ta
from interfaces import IEntrySignal, Signal
from mysignal import Direction

class TrendVolumeSignal(IEntrySignal):
    def generate(self, ctx_or_df, symbol: str, params: dict) -> Signal:
        if isinstance(ctx_or_df, pd.DataFrame):
            df = ctx_or_df
            ctx = {symbol: {"ohlcv": df}}
        else:
            ctx = ctx_or_df
            df = ctx[symbol]["ohlcv"]

        # 하이퍼옵트 파라미터
        ema_fast_period = params.get('ema_fast_period', 12)
        ema_slow_period = params.get('ema_slow_period', 26)
        vol_ma_period = params.get('vol_ma_period', 20)

        # === 지표 계산 ===
        ema_fast = ta.EMA(df, timeperiod=ema_fast_period)
        ema_slow = ta.EMA(df, timeperiod=ema_slow_period)
        vol_ma = df["volume"].rolling(vol_ma_period).mean()

        # === 진입 조건 ===
        cond = (
            (ema_fast > ema_slow) &
            (df["close"] > ema_fast) &
            (df["volume"] > vol_ma)
        )

        indexes = list(df.index[cond.fillna(False)])

        return Signal(
            name="trend_volume",
            indexes=indexes,
            direction=Direction.LONG,
            score=1.0,
            meta={
                "ema_fast_period": ema_fast_period,
                "ema_slow_period": ema_slow_period,
                "vol_ma_period": vol_ma_period,
            }
        )
