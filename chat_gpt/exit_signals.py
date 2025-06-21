# ===== /home/stongone123/freqtrade/src/strategies/exit_signals/__init__.py 시작 =====

# ===== /home/stongone123/freqtrade/src/strategies/exit_signals/__init__.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/exit_signals/sample_exit.py 시작 =====
from ..interfaces import IExitSignal
from ..signal import Signal, Direction

class SampleExit(IExitSignal):
    def generate(self, ctx) -> Signal:
        # TODO: 실제 청산 로직
        return Signal("SampleExit", Direction.EXIT, 0.0)

# ===== /home/stongone123/freqtrade/src/strategies/exit_signals/sample_exit.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/exit_signals/ema_cross_exit.py 시작 =====
import talib
from ..interfaces import IExitSignal
from ..signal import Signal, Direction

class EMACrossExitSignal(IExitSignal):
    def generate(self, ctx, position=None):
        close = ctx['close']
        fast_ema = talib.EMA(close, timeperiod=9)[-1]
        slow_ema = talib.EMA(close, timeperiod=21)[-1]

        # 단기 EMA가 장기 EMA 아래로 크로스될 때 청산 신호
        if fast_ema < slow_ema:
            score = 1.0
        else:
            score = 0.0

        return Signal("ema_cross_exit", Direction.EXIT, score)

# ---- 실전/주의/보완 ----
# - 9/21은 전형적 청산용 이평선(운영 시장/타임프레임별 실험 추천)
# - EMA 신호 단독 사용시 “가짜 반전”(노이즈) 많으니, 거래량·ATR 등 추가필터 병행 권장
# - 단기/장기 기준 변경 시, 진입 신호와 혼동되지 않게 주의!
# - 추세장, 변동성 높은 구간에선 슬리피지/익절 조기청산 위험

# ===== /home/stongone123/freqtrade/src/strategies/exit_signals/ema_cross_exit.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/exit_signals/roi_target_exit.py 시작 =====
from ..interfaces import IExitSignal
from ..signal import Signal, Direction

class ROITargetExitSignal(IExitSignal):
    def generate(self, ctx, position=None):
        # position: {'entry_price': float, 'current_price': float}
        entry = position['entry_price']
        price = position['current_price']

        # 목표수익률 4% (실전에서 최적화 추천)
        if (price - entry) / entry >= 0.04:
            score = 1.0
        else:
            score = 0.0

        return Signal("roi_target_exit", Direction.EXIT, score)

# ---- 실전/주의/보완 ----
# - 목표수익률(4%)은 실전 백테스트/리스크 성향에 따라 조정 필수!
# - 익절만 적용(손절은 따로 리스크 로직과 병행)
# - 급변동장에선 미체결/슬리피지(예상보다 덜 체결) 주의!
# - position dict 반드시 올바른 형태로 전달할 것!

# ===== /home/stongone123/freqtrade/src/strategies/exit_signals/roi_target_exit.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/exit_signals/trailing_stop_exit.py 시작 =====
from ..interfaces import IExitSignal
from ..signal import Signal, Direction

class TrailingStopExitSignal(IExitSignal):
    def __init__(self):
        self.highest = None  # 실전운영: 포지션별 관리(여러 종목이면 dict로!)

    def generate(self, ctx, position=None):
        price = position['current_price']
        entry = position['entry_price']
        # trailing % (2% 기본, 실전 최적화 추천)
        trail_perc = 0.02

        # 최고가 저장(포지션별, 실전 DB/메모리 연동 필수)
        if self.highest is None or price > self.highest:
            self.highest = price

        # 최고가 기준 trail_perc 하락 시 청산
        if price <= self.highest * (1 - trail_perc):
            score = 1.0
        else:
            score = 0.0

        return Signal("trailing_stop_exit", Direction.EXIT, score)

# ---- 실전/주의/보완 ----
# - trailing %는 전략/시장/변동성 따라 조정(0.5~3% 등)
# - self.highest는 포지션별/종목별 관리 필요(실전은 DB/상태관리 코드 연동!)
# - 강한 반등장/스캘핑은 trailing stop으로 불필요한 조기청산 위험 있음
# - DB/캐시 연동 없이 단일 인스턴스만 쓰면 포지션 동기화/오류 주의

# ===== /home/stongone123/freqtrade/src/strategies/exit_signals/trailing_stop_exit.py 끝 =====

