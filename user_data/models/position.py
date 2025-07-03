class Position:
    def __init__(self, symbol, entry_price, size, entry_time, fee=0.0, slippage=0.0, side="long", status="open"):
        self.symbol = symbol
        self.entry_price = entry_price
        self.size = size
        self.entry_time = entry_time
        self.fee = fee
        self.slippage = slippage
        self.side = side
        self.status = status

    def __repr__(self):
        return f"<Position {self.symbol} {self.size}@{self.entry_price} side={self.side} fee={self.fee} slippage={self.slippage}>"
