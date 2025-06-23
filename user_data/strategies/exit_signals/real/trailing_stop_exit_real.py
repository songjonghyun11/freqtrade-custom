from interfaces import IExitSignal
from mysignal import Signal, Direction

class TrailingStopExit(IExitSignal):
    def __init__(self):
        # 심볼별, 포지션별 최고가 관리 (dict)
        self.highest = {}

    def generate(self, ctx, symbol, params, position=None):
        price = position['current_price']
        entry = position['entry_price']
        trail_perc = params[symbol].get('trail_perc', 0.02)
        pos_id = position.get('position_id', symbol)  # 포지션 ID 없으면 symbol 기준

        # 포지션별 최고가 저장
        if pos_id not in self.highest or price > self.highest[pos_id]:
            self.highest[pos_id] = price

        # 최고가 기준 하락률 체크
        if price <= self.highest[pos_id] * (1 - trail_perc):
            score = 1.0
        else:
            score = 0.0

        return Signal("trailing_stop_exit", Direction.EXIT, score)
