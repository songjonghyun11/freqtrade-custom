import talib
from ..interfaces import IShortSignal
from ..signal import Signal, Direction

class RSIOverboughtSignal(IShortSignal):
    def generate(self, ctx):
        close = ctx['close']
        rsi = talib.RSI(close, timeperiod=14)[-1]

        # RSI 70 초과면 과매수→반전 숏 진입
        if rsi > 70:
            score = 1.0
        else:
            score = 0.0

        return Signal("rsi_overbought", Direction.SHORT, score)

# ---- 실전/주의/보완 ----
# - RSI(14)는 업계 표준, 과매수 기준(70)은 시장상황 따라 조정(60~80)
# - 과매수 지속 구간(‘역추세 장세’)에선 손실 위험 높음(추세장에선 오히려 매수세 폭등 가능!)
# - “반전+추세” 신호와 반드시 병행 실험 추천
# - 데이터 길이(최소 20~30) 미만이면 신호 불안정
# - 단독보단 볼린저밴드/모멘텀/거래량 등 보조 필터와 조합 추천
