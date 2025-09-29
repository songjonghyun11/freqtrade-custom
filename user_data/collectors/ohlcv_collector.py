import pandas as pd

class OHLCVCollector:
    def __init__(self, data_source):
        self.data_source = data_source

    def _normalize_df(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.sort_index()
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        else:
            df.index = df.index.tz_convert("UTC")
        return df[['open','high','low','close','volume']]

    def fetch(self, symbol: str, timeframe: str = '5m', start=None, end=None) -> pd.DataFrame:
        if hasattr(self.data_source, 'fetch_ohlcv'):
            ohlcv = self.data_source.fetch_ohlcv(symbol, timeframe, since=start, limit=1000)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True)  # ← utc=True
            df.set_index('datetime', inplace=True)
            return self._normalize_df(df)
        elif hasattr(self.data_source, 'get_ohlcv'):
            df = self.data_source.get_ohlcv(symbol, timeframe, start, end)
            return self._normalize_df(df)
        else:
            raise NotImplementedError("data_source에 fetch_ohlcv/get_ohlcv 필요")
