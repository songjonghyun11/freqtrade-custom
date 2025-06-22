import talib
from interfaces import IShortSignal
from signal import Signal, Direction

class BBReversionSignal(IShortSignal):
    def generate(self, ctx, symbol, params):
        close = ctx[symbol]['close']
        bb_period = params[symbol].get('bb_period', 20)
        bb_std = params[symbol].get('bb_std', 2.0)
        upper, middle, lower = talib.BBANDS(
            close,
            timeperiod=bb_period,
            nbdevup=bb_std,
            nbdevdn=bb_std
        )
        # 종가가 상단 밴드 돌파시 숏 진입
        if close[-1] > upper[-1]:
            score = 1.0
        else:
            score = 0.0
        return Signal("bb_reversion", Direction.SHORT, score)
