class PortfolioMDDManager:
    def __init__(self, mdd_limit_per_symbol=None):
        # symbol별 최고 평가금/최대 낙폭 관리
        self.max_equity = {}
        # symbol별 낙폭 기준, 없으면 0.10(10%)
        self.mdd_limit = mdd_limit_per_symbol or {}

    def apply(self, ctx, symbol, params, position):
        equity = ctx[symbol]['total_equity']  # 심볼별 전체 평가금(포지션+현금)
        if symbol not in self.max_equity or equity > self.max_equity[symbol]:
            self.max_equity[symbol] = equity

        mdd_limit = params[symbol].get('mdd_limit', 0.10)
        mdd = (self.max_equity[symbol] - equity) / self.max_equity[symbol]

        if mdd > mdd_limit:
            return {"action": "close_all", "reason": "portfolio_mdd"}
        else:
            return {"action": "hold"}
