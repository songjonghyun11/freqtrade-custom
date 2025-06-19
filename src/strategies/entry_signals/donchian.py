import numpy as np
from ..interfaces import IEntrySignal
from ..signal import Signal, Direction

class DonchianSignal(IEntrySignal):
    def generate(self, ctx):
        high = ctx['high']
        close = ctx['close']

        donchian_high = np.max(high[-20:])  # 20봉 최고가

        # 종가가 20일 최고가 돌파 시 롱 진입
        if close[-1] >= donchian_high:
            score = 1.0
        else:
            score = 0.0

        return Signal("donchian", Direction.LONG, score)

# ---- 실전/주의/보완 ----
# - 기간(20)은 논문/실전에서 자주 쓰는 값, 시장에 따라 조정
# - 횡보장/펌핑 직후엔 “돌파 후 실패(가짜 신호)” 주의!
# - 변동성 적은 종목에선 Donchian만 단독 사용 비추천(가짜 돌파 잦음)
# - 다양한 기간(10/20/55 등) 조합 백테스트 추천
# - 데이터 길이 30개 이상 필수 (최대 기간 + 10 이상)
