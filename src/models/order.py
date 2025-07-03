class Order:
    def __init__(self, symbol, price, quantity, side, order_type, fee=0.0, slippage=0.0, status="open", created_at=None):
        self.symbol = symbol
        self.price = price
        self.quantity = quantity
        self.side = side
        self.order_type = order_type
        self.fee = fee
        self.slippage = slippage
        self.status = status
        self.created_at = created_at

    def __repr__(self):
        return f"<Order {self.symbol} {self.side} {self.quantity}@{self.price} fee={self.fee} slippage={self.slippage}>"
    
class OrderbookData:
    def __init__(self, symbol, bids, asks, timestamp):
        self.symbol = symbol
        self.bids = bids
        self.asks = asks
        self.timestamp = timestamp
    def __repr__(self):
        return f"<OrderbookData {self.symbol} bids={len(self.bids)} asks={len(self.asks)} timestamp={self.timestamp}>"

class FearGreedData:
    def __init__(self, timestamp, value, value_classification):
        self.timestamp = timestamp
        self.value = value
        self.value_classification = value_classification
    def __repr__(self):
        return f"<FearGreedData {self.timestamp} value={self.value} ({self.value_classification})>"

class FundingRateData:
    def __init__(self, symbol, rate, timestamp):
        self.symbol = symbol
        self.rate = rate
        self.timestamp = timestamp
    def __repr__(self):
        return f"<FundingRateData {self.symbol} rate={self.rate} timestamp={self.timestamp}>"

class SocialMediaData:
    def __init__(self, symbol, content, sentiment, timestamp):
        self.symbol = symbol
        self.content = content
        self.sentiment = sentiment
        self.timestamp = timestamp
    def __repr__(self):
        return f"<SocialMediaData {self.symbol} sentiment={self.sentiment} timestamp={self.timestamp}>"

class YouTubeData:
    def __init__(self, symbol, title, views, timestamp):
        self.symbol = symbol
        self.title = title
        self.views = views
        self.timestamp = timestamp
    def __repr__(self):
        return f"<YouTubeData {self.symbol} title={self.title} views={self.views} timestamp={self.timestamp}>"

class ChartVisionData:
    def __init__(self, symbol, chart_url, prediction, timestamp):
        self.symbol = symbol
        self.chart_url = chart_url
        self.prediction = prediction
        self.timestamp = timestamp
    def __repr__(self):
        return f"<ChartVisionData {self.symbol} prediction={self.prediction} timestamp={self.timestamp}>"
