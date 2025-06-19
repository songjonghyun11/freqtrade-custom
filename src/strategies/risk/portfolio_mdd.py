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
