import talib
from ..interfaces import IEntrySignal
from ..signal import Signal, Direction

class EMACrossoverSignal(IEntrySignal):
    def generate(self, ctx):
        close = ctx['close']

        fast_ema = talib.EMA(close, timeperiod=12)[-1]
        slow_ema = talib.EMA(close, timeperiod=26)[-1]

        # 단기(12) > 장기(26)일 때 롱 진입
        if fast_ema > slow_ema:
            score = 1.0
        else:
            score = 0.0

        return Signal("ema_crossover", Direction.LONG, score)

# ---- 실전/주의/보완 ----
# - 12/26은 전형적 기본값(비트/주식 모두 검증)
# - “데드크로스/골든크로스” 신호가 시장 전환점에 적중하지 않을 수 있음(특히 횡보장!)
# - 노이즈 많은 구간엔 “추가 필터(예: 거래량, ATR)” 연계 추천
# - 빠른 신호=거래 횟수↑, 슬리피지·수수료 영향 커질 수 있음
# - 반드시 EMA/SMA 혼용 여부 일관성 체크!
