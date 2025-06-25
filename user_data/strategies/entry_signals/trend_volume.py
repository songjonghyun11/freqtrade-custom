import pandas as pd
import talib.abstract as ta
from interfaces import IEntrySignal

class TrendVolumeSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        df = ctx

        # 파라미터 가져오기 (없으면 기본값)
        ema_fast_period = params.get('ema_fast_period', 12)
        ema_slow_period = params.get('ema_slow_period', 26)
        vol_ma_period = params.get('vol_ma_period', 20)

        # === 지표 계산 ===
        ema_fast = ta.EMA(df, timeperiod=ema_fast_period)
        ema_slow = ta.EMA(df, timeperiod=ema_slow_period)
        vol_ma = df["volume"].rolling(vol_ma_period).mean()

        # === 조건 ===
        cond = (
            (ema_fast > ema_slow) &
            (df["close"] > ema_fast) &
            (df["volume"] > vol_ma)
        )

        return cond.fillna(False)
