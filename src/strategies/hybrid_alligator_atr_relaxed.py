from freqtrade.strategy import IStrategy
from freqtrade.strategy.parameters import RealParameter, IntParameter
import talib.abstract as ta
import pandas as pd
from pandas import DataFrame

from modules.entry_signal import EntrySignal
from modules.exit_signal import ExitSignal
from modules.risk_manager import RiskManager

class HybridAlligatorATRRelaxedStrategy(IStrategy):
    # 기본 설정
    timeframe = '5m'
    startup_candle_count = 50

    # Dynamic stop-loss ATR multiplier (Hyperopt 대상)
    sl_atr_multiplier = RealParameter(
        0.5, 3.0, default=1.5, space='sell', optimize=True, load=True
    )

    minimal_roi = {
        "0":   0.245,
        "26":  0.048,
        "50":  0.021,
        "121": 0
    }

    # 기본 stoploss (백업용)
    stoploss = -0.23
    stoploss_param = RealParameter(
        -0.10, -0.01, default=-0.02441,
        space='sell', optimize=True, load=True
    )

    trailing_stop = True
    trailing_stop_positive = 0.03
    trailing_stop_positive_offset = 0.05
    trailing_only_offset_is_reached = False

    process_only_new_candles = True
    use_custom_stoploss = True
    # can_long / can_short 는 __init__에서 trading_mode에 따라 설정

    # Entry signal 파라미터 (Hyperopt 대상)
    atr_period      = IntParameter(8, 21,  default=14,  space='buy', optimize=True, load=True)
    vol_multiplier  = RealParameter(1.0, 3.0, default=1.2,  space='buy', optimize=True, load=True)
    volat_threshold = RealParameter(0.003,0.02, default=0.005, space='buy', optimize=True, load=True)
    high_lookback   = IntParameter(1, 7,   default=3,    space='buy', optimize=True, load=True)

    def __init__(self, config: dict):
        super().__init__(config)
        # Spot vs Futures 분기: futures 모드면 숏 허용, 아니면 롱만
        trading_mode = config.get("trading_mode", "spot").lower()
        self.can_long  = True
        self.can_short = trading_mode == "futures"

        # 모듈에 전달할 파라미터 딕셔너리 생성
        params = {
            "atr_period":      int(self.atr_period.value),
            "vol_multiplier":  float(self.vol_multiplier.value),
            "volat_threshold": float(self.volat_threshold.value),
            "high_lookback":   int(self.high_lookback.value),
            "sl_atr_multiplier": float(self.sl_atr_multiplier.value),
        }
        self.entry_module = EntrySignal(params)
        self.exit_module  = ExitSignal(params)
        self.risk_module  = RiskManager(params["sl_atr_multiplier"])

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Alligator 지표 계산
        hl2 = (dataframe['high'] + dataframe['low']) / 2
        dataframe['jaw']   = pd.Series(ta.EMA(hl2, timeperiod=13), index=dataframe.index).shift(8)
        dataframe['teeth'] = pd.Series(ta.EMA(hl2, timeperiod=8),  index=dataframe.index).shift(5)
        dataframe['lips']  = pd.Series(ta.EMA(hl2, timeperiod=5),  index=dataframe.index).shift(3)

        # ADX/DI
        dataframe['adx']     = ta.ADX(dataframe, timeperiod=14)
        dataframe['plusdi']  = ta.PLUS_DI(dataframe, timeperiod=14)
        dataframe['minusdi'] = ta.MINUS_DI(dataframe, timeperiod=14)

        # ATR 및 볼륨 MA
        dataframe['atr']    = ta.ATR(dataframe, timeperiod=self.atr_period.value)
        dataframe['vol_ma'] = dataframe['volume'].rolling(10).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        if dataframe.empty:
            return dataframe

        # EntrySignal 모듈 사용
        long_signals  = self.entry_module.generate_long(dataframe)
        dataframe.loc[long_signals, 'enter_long'] = 1

        if self.can_short:
            short_signals = self.entry_module.generate_short(dataframe)
            dataframe.loc[short_signals, 'enter_short'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # ExitSignal 모듈 사용
        exit_long_signals  = self.exit_module.generate_long(dataframe)
        dataframe.loc[exit_long_signals, 'exit_long'] = 1

        if self.can_short:
            exit_short_signals = self.exit_module.generate_short(dataframe)
            dataframe.loc[exit_short_signals, 'exit_short'] = 1

        return dataframe

    def custom_stoploss(self, pair, trade, current_time, current_rate, current_profit, **kwargs) -> float:
        # 1) 원본 OHLCV 데이터 불러오기
        df = self.dp.get_pair_dataframe(pair)

        # 2) ATR 을 talib 로 재계산 (populate_indicators 파라미터와 일치)
        period = int(self.atr_period.value)
        atr_series = ta.ATR(df, timeperiod=period)
        atr = atr_series.iloc[-1]

        # 3) 동적 손절가 계산 (entry_price - multiplier * atr)
        stoploss_price = self.risk_module.calculate_stoploss(trade.open_rate, atr)

        # 4) 비율로 변환하여 음수 반환
        return stoploss_price / trade.open_rate - 1
