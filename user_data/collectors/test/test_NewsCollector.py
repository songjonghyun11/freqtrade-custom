from news import NewsCollector

collector = NewsCollector(data_dir='data')

symbol = "BTC_USDT"
timestamp = 1704067200  # 샘플 데이터와 일치시켜야 함!

try:
    news_list = collector.fetch_news(symbol=symbol, timestamp=timestamp)
    print(f"[TEST RESULT] {news_list}")
except Exception as e:
    print(f"[ERROR] {e}")
