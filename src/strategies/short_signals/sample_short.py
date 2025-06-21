from ..interfaces import IShortSignal
from ..signal import Signal, Direction

class SampleShort(IShortSignal):
    def generate(self, ctx, symbol, params) -> Signal:
        # TODO: 실제 숏 진입 로직
        return Signal("SampleShort", Direction.SHORT, 0.0)
