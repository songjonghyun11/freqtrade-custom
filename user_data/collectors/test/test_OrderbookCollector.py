from orderbook import OrderbookCollector

collector = OrderbookCollector(data_dir='data')

symbol = "BTC_USDT"
timestamp = 1704067200  # 샘플 데이터와 일치!

try:
    result = collector.fetch(symbol=symbol, timestamp=timestamp)
    print(f"[TEST RESULT] {result}")
except Exception as e:
    print(f"[ERROR] {e}")
