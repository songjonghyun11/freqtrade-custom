import talib
from ..interfaces import IExitSignal
from ..signal import Signal, Direction

class EMACrossExitSignal(IExitSignal):
    def generate(self, ctx, position=None):
        close = ctx['close']
        fast_ema = talib.EMA(close, timeperiod=9)[-1]
        slow_ema = talib.EMA(close, timeperiod=21)[-1]

        # 단기 EMA가 장기 EMA 아래로 크로스될 때 청산 신호
        if fast_ema < slow_ema:
            score = 1.0
        else:
            score = 0.0

        return Signal("ema_cross_exit", Direction.EXIT, score)

# ---- 실전/주의/보완 ----
# - 9/21은 전형적 청산용 이평선(운영 시장/타임프레임별 실험 추천)
# - EMA 신호 단독 사용시 “가짜 반전”(노이즈) 많으니, 거래량·ATR 등 추가필터 병행 권장
# - 단기/장기 기준 변경 시, 진입 신호와 혼동되지 않게 주의!
# - 추세장, 변동성 높은 구간에선 슬리피지/익절 조기청산 위험
