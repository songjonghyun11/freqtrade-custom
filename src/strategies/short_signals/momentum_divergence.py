import talib
from ..interfaces import IShortSignal
from ..signal import Signal, Direction

class MomentumDivergenceSignal(IShortSignal):
    def generate(self, ctx):
        close = ctx['close']
        macd, macdsignal, _ = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)

        # 가격은 신고가, MACD는 저점(다이버전스) 발생 시 반전 숏 신호
        if close[-1] > max(close[-10:-1]) and macd[-1] < macd[-2]:
            score = 1.0
        else:
            score = 0.0

        return Signal("momentum_divergence", Direction.SHORT, score)

# ---- 실전/주의/보완 ----
# - “가격은 고점 돌파, 모멘텀(MACD)은 약화” → 다이버전스 전형적 신호
# - 구간(10봉)·모멘텀지표(MACD/RSI 등) 실험으로 최적화 추천
# - 단독 신호는 “상승장/펌핑장”에선 위협, 필터 조합(거래량/캔들) 필요
# - 신호 연속 발생 시 “중복 진입/과매매” 주의!
# - 조건 단순화 → 실제론 구간/지표 더 세분화해 실험
