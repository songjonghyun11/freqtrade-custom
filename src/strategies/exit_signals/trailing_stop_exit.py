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
