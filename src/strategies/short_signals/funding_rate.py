from ..interfaces import IShortSignal
from ..signal import Signal, Direction

class FundingRateSignal(IShortSignal):
    def generate(self, ctx):
        funding = ctx['funding']  # 실전: 최근 펀딩비(%), float
        # 기준값: 0.05% 이상이면 비정상(롱 쏠림)→역추세 숏 진입
        if funding > 0.0005:
            score = 1.0
        else:
            score = 0.0

        return Signal("funding_rate", Direction.SHORT, score)

# ---- 실전/주의/보완 ----
# - funding은 실제 거래소에서 주기별 받아와야 함(FTX, Binance, Bybit 등)
# - 기준치(0.05%)는 시장/코인별 차이 큼(역전/급등 전 데이터 필수 분석)
# - “롱 쏠림”에만 숏, “숏 쏠림”엔 반대 신호(매수)도 확장 가능
# - 단독 신호 위험, 오더북/심리/가격패턴 등과 반드시 병행 실험
# - 극단적 펀딩 뒤엔 반대 급등락도 잦음(시장 패닉 주의!)
