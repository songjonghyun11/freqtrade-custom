from interfaces import IEntrySignal
from signal import Signal, Direction

class AISignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        pass
