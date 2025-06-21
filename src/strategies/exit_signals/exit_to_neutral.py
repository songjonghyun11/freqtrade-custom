from ..interfaces import IExitSignal
from ..signal import Signal, Direction

class ExitToNeutralSignal(IExitSignal):
    def generate(self, ctx, symbol, params, position=None):
        # 예시: Aggregator score가 너무 낮거나, 관망 신호 조건 충족 시
        aggregator_score = ctx[symbol].get('aggregator_score', 0.0)
        threshold = params[symbol].get('neutral_threshold', 0.3)
        if aggregator_score < threshold:
            score = 1.0
        else:
            score = 0.0
        return Signal("exit_to_neutral", Direction.EXIT, score)
