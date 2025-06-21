from ..interfaces import IEntrySignal
from ..signal import Signal, Direction

class NewsSentimentSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        pass
