from ..interfaces import IEntrySignal
from ..signal import Signal, Direction

class MLSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        pass
