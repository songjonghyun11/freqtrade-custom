import numpy as np
from interfaces import IEntrySignal
from mysignal import Signal, Direction

class DonchianSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        high = ctx[symbol]['high']
        close = ctx[symbol]['close']

        # 심볼별 파라미터 (없으면 디폴트)
        period = params[symbol].get('donchian_period', 20)

        donchian_high = np.max(high[-period:])  # 기간 내 최고가

        # 종가가 최고가 돌파 시 롱 진입
        if close[-1] >= donchian_high:
            score = 1.0
        else:
            score = 0.0

        return Signal("donchian", Direction.LONG, score)
