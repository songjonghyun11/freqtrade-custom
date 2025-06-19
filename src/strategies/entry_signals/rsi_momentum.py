import talib
from ..interfaces import IEntrySignal
from ..signal import Signal, Direction

class RSIMomentumSignal(IEntrySignal):
    def generate(self, ctx):
        close = ctx['close']
        rsi = talib.RSI(close, timeperiod=14)[-1]

        # RSI 35~55 구간에서 반등(상승 모멘텀) 포착
        if 35 < rsi < 55:
            score = 1.0
        else:
            score = 0.0

        return Signal("rsi_momentum", Direction.LONG, score)

# ---- 실전/주의/보완 ----
# - RSI 14는 업계 표준, 실전에서는 10~21 구간도 실험!
# - 35~55는 “단기 반등/추세전환” 구간(시장 상황에 맞춰 범위 조정)
# - 과매수(70↑)/과매도(30↓) 신호와 같이 쓰면 효과적
# - 단독 사용 시 “가짜 신호” 위험→추가 필터(거래량, 지지/저항) 추천
# - 데이터 길이(최소 20~30개) 안 되면 신호 오류!
