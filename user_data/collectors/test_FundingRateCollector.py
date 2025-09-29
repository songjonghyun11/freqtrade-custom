from funding_rate import FundingRateCollector

collector = FundingRateCollector(mode='backtest', data_dir='data')

symbol = "BTC_USDT"
timestamp = 1704067200  # 샘플 데이터와 일치시켜야 함!

try:
    result = collector.fetch(symbol=symbol, timestamp=timestamp)
    print(f"[TEST RESULT] {result}")
except Exception as e:
    print(f"[ERROR] {e}")
