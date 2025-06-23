import numpy as np
import talib
from interfaces import IEntrySignal
from mysignal import Signal, Direction

class AlligatorATRSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        # 심볼별 데이터
        close = ctx[symbol]['close']
        high = ctx[symbol]['high']
        low = ctx[symbol]['low']

        # 심볼별 파라미터 (없으면 디폴트)
        ema_jaw = params[symbol].get('ema_jaw', 13)
        ema_teeth = params[symbol].get('ema_teeth', 8)
        ema_lips = params[symbol].get('ema_lips', 5)
        atr_period = params[symbol].get('atr_period', 14)
        atr_threshold = params[symbol].get('atr_threshold', 0.01)

        # === Alligator(EMA 13/8/5)
        jaw = talib.EMA(close, timeperiod=ema_jaw)[-1]
        teeth = talib.EMA(close, timeperiod=ema_teeth)[-1]
        lips = talib.EMA(close, timeperiod=ema_lips)[-1]

        # === ATR: 변동성 체크
        atr = talib.ATR(high, low, close, timeperiod=atr_period)[-1]

        # === 진입조건 ===
        if lips > teeth > jaw and close[-1] > jaw and atr > atr_threshold:
            score = 1.0
        else:
            score = 0.0

        return Signal("alligator_atr", Direction.LONG, score)
