# sample_data_source.py
import pandas as pd

class SampleDataSource:
    def get_ohlcv(self, symbol, timeframe, start=None, end=None):
        # 실제로는 CSV/DB에서 읽겠지만, 여기서는 더미 데이터 생성
        data = {
            'open': [100, 102, 101],
            'high': [105, 103, 106],
            'low': [99, 100, 100],
            'close': [104, 101, 105],
            'volume': [1.0, 2.0, 1.5],
        }
        index = pd.date_range("2025-01-01", periods=3, freq="5min")
        df = pd.DataFrame(data, index=index)
        return df
