from chart_vision import ChartVisionCollector

collector = ChartVisionCollector(mode='backtest', data_dir='data')

symbol = "BTC_USDT"
timestamp = "2025-01-01T09:00:00"  # 네 데이터 파일에 있는 실제 timestamp로 교체해야 함!

try:
    result = collector.fetch(symbol=symbol, timestamp=timestamp)
    print(f"[TEST RESULT] {result}")
except Exception as e:
    print(f"[ERROR] {e}")
