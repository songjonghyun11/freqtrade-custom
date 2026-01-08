from ohlcv_collector import OHLCVCollector
from data_source import SampleDataSource

collector = OHLCVCollector(data_source=SampleDataSource())
symbol = "BTC_USDT"
timeframe = "5m"

try:
    df = collector.fetch(symbol=symbol, timeframe=timeframe)
    print("[TEST RESULT]\n", df)
except Exception as e:
    print(f"[ERROR] {e}")
