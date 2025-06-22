from interfaces import IEntrySignal
from mysignal import Signal, Direction

class AISignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        pass
