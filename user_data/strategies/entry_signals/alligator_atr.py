from pandas import Series
import numpy as np
import pandas as pd
import talib.abstract as ta
from interfaces import IEntrySignal
from pandas import DataFrame

class AlligatorATRSignal(IEntrySignal):
    def generate(self, df: DataFrame, symbol: str, params) -> Series:
    # ✅ 하이퍼옵트용 dict 처리 or 단일 파라미터 처리
        if isinstance(params, dict):
            ema_jaw = params.get('ema_jaw', 13)
            ema_teeth = params.get('ema_teeth', 8)
            ema_lips = params.get('ema_lips', 5)
            atr_period = params.get('atr_period', 14)
        else:
            # fallback: 실전용 기본값
            ema_jaw = 13
            ema_teeth = 8
            ema_lips = 5
            atr_period = 14

        hl2 = (df["high"] + df["low"]) / 2

        jaw = pd.Series(ta.EMA(hl2, timeperiod=ema_jaw), index=df.index).shift(8)
        teeth = pd.Series(ta.EMA(hl2, timeperiod=ema_teeth), index=df.index).shift(5)
        lips = pd.Series(ta.EMA(hl2, timeperiod=ema_lips), index=df.index).shift(3)
        atr = ta.ATR(df, timeperiod=atr_period)

    # 예시 조건: Alligator가 벌어지고 상승 추세 + 변동성 필터
        entry = (
            (lips > teeth) &
            (teeth > jaw) &
            (df['close'] > lips) &
            (atr > 0)
    )

        return entry.fillna(False)
 