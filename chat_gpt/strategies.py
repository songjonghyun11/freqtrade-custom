# ===== /home/stongone123/freqtrade/src/strategies/hybrid_alligator_atr_relaxed.py 시작 =====
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

# ===== /home/stongone123/freqtrade/src/strategies/hybrid_alligator_atr_relaxed.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/__init__.py 시작 =====

# ===== /home/stongone123/freqtrade/src/strategies/__init__.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/strategy_orchestrator.py 시작 =====
from typing import List
from .interfaces import IEntrySignal, IShortSignal, IExitSignal, IRiskManager
from .signal import Signal

class StrategyOrchestrator:
    def __init__(self,
        entry_signals: List[IEntrySignal],
        short_signals: List[IShortSignal],
        exit_signals: List[IExitSignal],
        risk_managers: List[IRiskManager],
    ):
        self._entries = entry_signals
        self._shorts  = short_signals
        self._exits   = exit_signals
        self._risks   = risk_managers

    def decide_long(self, ctx):
        signals = [s.generate(ctx) for s in self._entries]
        return max(signals, key=lambda x: x.score) if signals else False

    def decide_short(self, ctx):
        signals = [s.generate(ctx) for s in self._shorts]
        return max(signals, key=lambda x: x.score) if signals else False

    def decide_exit(self, ctx):
        signals = [s.generate(ctx) for s in self._exits]
        return max(signals, key=lambda x: x.score) if signals else False

    def assess_risk(self, ctx):
        signals = [s.generate(ctx) for s in self._risks]
        return max(signals, key=lambda x: x.score) if signals else False

# ===== /home/stongone123/freqtrade/src/strategies/strategy_orchestrator.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/interfaces.py 시작 =====
from abc import ABC, abstractmethod
from typing import Any
from .signal import Signal

class IEntrySignal(ABC):
    @abstractmethod
    def generate(self, ctx: Any) -> Signal:
        """롱 진입 신호 생성"""
        ...

class IShortSignal(ABC):
    @abstractmethod
    def generate(self, ctx: Any) -> Signal:
        """숏 진입 신호 생성"""
        ...

class IExitSignal(ABC):
    @abstractmethod
    def generate(self, ctx: Any, position: Any = None) -> Signal:
        """청산 신호 생성"""
        ...

class IRiskManager(ABC):
    @abstractmethod
    def apply(self, ctx: Any, position: Any) -> Any:
        """리스크 평가 및 주문 객체(Order) 리턴"""
        ...

# ======== [확장] Allocator & AnomalyDetector 인터페이스 추가 ========

class IAllocator(ABC):
    @abstractmethod
    def decide_allocation(self, ctx: Any) -> dict:
        """포지션 배분 결정"""
        ...

class IAnomalyDetector(ABC):
    @abstractmethod
    def detect(self, ctx: Any) -> bool:
        """이상 감지"""
        ...

# ===== /home/stongone123/freqtrade/src/strategies/interfaces.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/signal.py 시작 =====
from enum import Enum

class Direction(Enum):
    LONG = "long"
    SHORT = "short"
    EXIT = "exit"

class Signal:
    def __init__(self, name: str, direction: Direction, score: float):
        self.name = name
        self.direction = direction
        self.score = score

# ===== /home/stongone123/freqtrade/src/strategies/signal.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/signal_aggregator.py 시작 =====
# src/strategies/signal_aggregator.py

from typing import List

class SignalAggregator:
    @staticmethod
    def decide_long(ctx: dict) -> List[dict]:
        symbol = ctx.get("symbol", "UNKNOWN")
        return [{"strategy": "mock_long", "symbol": symbol, "score": 0.9}]

    @staticmethod
    def decide_short(ctx: dict) -> List[dict]:
        symbol = ctx.get("symbol", "UNKNOWN")
        return [{"strategy": "mock_short", "symbol": symbol, "score": 0.85}]

# ===== /home/stongone123/freqtrade/src/strategies/signal_aggregator.py 끝 =====

