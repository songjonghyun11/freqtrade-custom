from ..interfaces import IExitSignal
from ..signal import Signal, Direction

class SampleExit(IExitSignal):
    def generate(self, ctx) -> Signal:
        # TODO: 실제 청산 로직
        return Signal("SampleExit", Direction.EXIT, 0.0)
