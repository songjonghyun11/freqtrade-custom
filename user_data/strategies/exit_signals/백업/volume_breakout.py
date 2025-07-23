from interfaces import IEntrySignal
from mysignal import Signal, Direction

class VolumeBreakoutSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        pass
