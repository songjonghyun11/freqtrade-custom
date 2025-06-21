from ..interfaces import IEntrySignal
from ..signal import Signal, Direction

class VolumeBreakoutSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        pass
