from freqtrade.strategy import IStrategy
from pandas import DataFrame

class DebugUnconditionalStrategy(IStrategy):
    """
    모든 캔들마다 무조건 진입(enter_long=1)만 테스트
    """
    timeframe = '5m'
    startup_candle_count = 0

    # CONFIG 없이도 백테스트 통과시키기 위한 기본값
    minimal_roi = {"0": 0}
    stoploss = -0.10
    trailing_stop = False
    process_only_new_candles = True

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 지표 없이 바로 반환
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 모든 캔들마다 진입 신호 생성
        dataframe['enter_long'] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # 종료 신호는 사용하지 않음
        return dataframe
