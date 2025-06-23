from interfaces import IEntrySignal
from mysignal import Signal, Direction

class NewsSentimentSignal(IEntrySignal):
    def generate(self, ctx, symbol, params):
        pass
