import numpy as np
from ..interfaces import IEntrySignal
from ..signal import Signal, Direction

class VWAPReversionSignal(IEntrySignal):
    def generate(self, ctx):
        close = ctx['close']
        volume = ctx.get('volume', np.ones_like(close))
        vwap = np.sum(close[-20:] * volume[-20:]) / np.sum(volume[-20:])

        # 종가가 VWAP 위로 돌파 시 롱 진입
        if close[-1] > vwap:
            score = 1.0
        else:
            score = 0.0

        return Signal("vwap_reversion", Direction.LONG, score)

# ---- 실전/주의/보완 ----
# - VWAP(20봉)은 “평균가” 기준, 단기(5/10), 중기(50) 등 다양한 실험 필요
# - 볼륨 데이터 없으면 신호 왜곡 가능성 높음(실전 DB 연동 필수)
# - 단독 신호보다는 “반등+추세+지지” 등 다른 신호와 조합 추천
# - 급락/급등 직후에는 평균값만 보고 진입하면 손실 위험!
# - 실전 백테스트로 돌파 구간/실패 구간 반드시 분석!
