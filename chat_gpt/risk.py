# ===== /home/stongone123/freqtrade/src/strategies/risk/__init__.py 시작 =====

# ===== /home/stongone123/freqtrade/src/strategies/risk/__init__.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/risk/sample_risk.py 시작 =====
from ..interfaces import IRiskManager
from ..signal import Signal, Direction

class SampleRisk(IRiskManager):
    def generate(self, ctx) -> Signal:
        # TODO: 실제 리스크 평가 로직
        return Signal("SampleRisk", Direction.RISK, 0.0)

# ===== /home/stongone123/freqtrade/src/strategies/risk/sample_risk.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/risk/dynamic_stoploss.py 시작 =====
from ..interfaces import IRiskManager

class DynamicStoploss(IRiskManager):
    def apply(self, ctx, position):
        # position: {'entry_price': float, 'current_price': float}
        entry = position['entry_price']
        price = position['current_price']

        # 손절(기본 2%): 실전 최적화/변동성/시장 맞춤 조정!
        stoploss = entry * 0.98

        if price < stoploss:
            return {"action": "close", "reason": "dynamic_stoploss"}
        else:
            return {"action": "hold"}

# ---- 실전/주의/보완 ----
# - 손절폭(2%)은 시장/전략별 유연하게 튜닝!
# - 손절만 담당, 익절은 청산로직과 별도 처리
# - position dict 구조 확실하게 맞출 것!
# - 급락/펌핑 등 돌발 변동시 “시장가 강제 청산” 트리거 가능

# ===== /home/stongone123/freqtrade/src/strategies/risk/dynamic_stoploss.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/risk/portfolio_mdd.py 시작 =====
class PortfolioMDDManager:
    def __init__(self, mdd_limit=0.10):  # MDD 10% 기본
        self.max_equity = None
        self.mdd_limit = mdd_limit

    def apply(self, ctx, position):
        equity = ctx['total_equity']  # 전체 자산/현금+포지션 평가액

        # 최고 자산 기록
        if self.max_equity is None or equity > self.max_equity:
            self.max_equity = equity

        mdd = (self.max_equity - equity) / self.max_equity
        # 최대 낙폭(MDD) 10% 넘으면 모든 포지션 강제 청산
        if mdd > self.mdd_limit:
            return {"action": "close_all", "reason": "portfolio_mdd"}
        else:
            return {"action": "hold"}

# ---- 실전/주의/보완 ----
# - mdd_limit(10%)은 펀드/자산관리 업계 표준, 실전엔 투자성향에 맞춰 조정
# - equity(총평가금) 산정 공식 정확하게 맞춰야 함(포지션 평가/현금 포함)
# - 단일 인스턴스 운영시, 리셋/초기화 오류 주의
# - 급락장엔 한 번에 모든 포지션 청산될 수 있으니, 위험분산/분할청산 조합도 추천!
# - 실전은 DB/캐시 연동, 백테스트/실거래에선 연동 체크

# ===== /home/stongone123/freqtrade/src/strategies/risk/portfolio_mdd.py 끝 =====

