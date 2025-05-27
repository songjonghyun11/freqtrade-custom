from ..interfaces import IRiskManager
from ..signal import Signal, Direction

class SampleRisk(IRiskManager):
    def generate(self, ctx) -> Signal:
        # TODO: 실제 리스크 평가 로직
        return Signal("SampleRisk", Direction.RISK, 0.0)
