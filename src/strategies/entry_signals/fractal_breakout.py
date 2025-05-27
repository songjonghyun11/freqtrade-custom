from ..interfaces import IEntrySignal
from ..signal import Signal, Direction

class FractalBreakout(IEntrySignal):
    def generate(self, ctx) -> Signal:
        # TODO: 실제 로직 구현
        return Signal("FractalBreakout", Direction.LONG, 0.0)
