from fear_greed import FearGreedCollector

collector = FearGreedCollector(mode='backtest', data_dir='data')

symbol = "BTC_USDT"
timestamp = 1704067200  # 네 데이터 파일에 실제 있는 timestamp로 교체!

try:
    result = collector.fetch(symbol=symbol, timestamp=timestamp)
    print(f"[TEST RESULT] {result}")
except Exception as e:
    print(f"[ERROR] {e}")
