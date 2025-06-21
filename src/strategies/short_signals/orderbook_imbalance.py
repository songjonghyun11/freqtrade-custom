from ..interfaces import IShortSignal
from ..signal import Signal, Direction

class OrderbookImbalanceSignal(IShortSignal):
    def generate(self, ctx, symbol, params):
        bid_vol = ctx[symbol]['bid_vol']
        ask_vol = ctx[symbol]['ask_vol']
        ratio = params[symbol].get('orderbook_ratio', 1.5)
        if ask_vol > ratio * bid_vol:
            score = 1.0
        else:
            score = 0.0
        return Signal("orderbook_imbalance", Direction.SHORT, score)
