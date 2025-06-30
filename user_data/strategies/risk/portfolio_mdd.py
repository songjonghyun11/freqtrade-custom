from interfaces import IRiskManager
import pandas as pd

class PortfolioMDDRisk(IRiskManager):
    def __init__(self, mdd_limit=0.10):
        self.mdd_limit = mdd_limit
        self.max_equity = None

    def adjust_stoploss(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        # 실제 포트폴리오 평가금 등 로직은 네 상황에 맞게 구현!
        # 아래는 최소 템플릿 (여기서는 None 리턴, 실제 구현은 필요에 따라) #2️⃣ 실전 실거래 자동매매 단계에서
            #실시간 잔고/포트폴리오 평가금을 받아서
          #현재 계좌 낙폭(MDD), 실현손익, 실시간 위험 분석을 직접 체크할 때 #즉,
         #실전 자동매매 루프, Collector, 실전 메인 봇, 실시간 트레이드 엔진과 연결하는 시점이 오면
             #이때 adjust_stoploss 함수 내부에 “실제 평가금/잔고/리스크 계산”을 넣으면 됨!
        return None

    def apply(self, df: pd.DataFrame, symbol: str, params: dict):
        mdd_limit = params.get('mdd_limit', 0.10)
        if "total_equity" not in df.columns:
            return pd.Series([False] * len(df), index=df.index)
        if self.max_equity is None:
            self.max_equity = df["total_equity"].cummax()
        mdd = (self.max_equity - df["total_equity"]) / self.max_equity
        return (mdd > mdd_limit).fillna(False)
    
    def calculate_stoploss(self, *args, **kwargs):
        # 반드시 있어야 함! 내용은 상관없음
        return None
