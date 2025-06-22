from interfaces import IExitSignal
from signal import Signal, Direction

class SampleExit(IExitSignal):
    def generate(self, ctx, symbol, params) -> Signal:
        # TODO: 실제 청산 로직 (여기에 추가)
        return Signal("SampleExit", Direction.EXIT, 0.0)
