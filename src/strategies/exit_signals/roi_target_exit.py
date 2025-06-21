from ..interfaces import IExitSignal
from ..signal import Signal, Direction

class ROITargetExitSignal(IExitSignal):
    def generate(self, ctx, symbol, params, position=None):
        entry = position['entry_price']
        price = position['current_price']
        # 심볼별 목표 수익률 (없으면 4%)
        roi_target = params[symbol].get('roi_target', 0.04)

        if (price - entry) / entry >= roi_target:
            score = 1.0
        else:
            score = 0.0

        return Signal("roi_target_exit", Direction.EXIT, score)
