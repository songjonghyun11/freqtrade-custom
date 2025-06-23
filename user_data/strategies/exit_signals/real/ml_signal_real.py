from interfaces import IEntrySignal
from mysignal import Signal, Direction

class MLSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        pass
