# ohlcv_collector.py
import pandas as pd

class OHLCVCollector:
    def __init__(self, data_source):
        """
        data_source: CCXT(실전), DB(백테스트), csv 등에서 데이터 가져오는 객체
        """
        self.data_source = data_source

    def fetch(self, symbol: str, timeframe: str = '5m', start=None, end=None) -> pd.DataFrame:
        """
        symbol: 코인 심볼(예: 'BTC/USDT')
        timeframe: 봉 간격(예: '5m', '1h', '1d')
        start, end: datetime 또는 timestamp(선택)
        return: OHLCV 데이터 DataFrame
        """
        # 실전: CCXT 연동
        # 예시 코드 (ccxt)
        if hasattr(self.data_source, 'fetch_ohlcv'):
            ohlcv = self.data_source.fetch_ohlcv(symbol, timeframe, since=start, limit=1000)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('datetime', inplace=True)
            return df[['open', 'high', 'low', 'close', 'volume']]
        # 백테스트/CSV 등은 아래와 같이 구현 (데이터 소스에 따라)
        elif hasattr(self.data_source, 'get_ohlcv'):
            df = self.data_source.get_ohlcv(symbol, timeframe, start, end)
            return df[['open', 'high', 'low', 'close', 'volume']]
        else:
            raise NotImplementedError("data_source에 fetch_ohlcv/get_ohlcv 메서드 필요")
