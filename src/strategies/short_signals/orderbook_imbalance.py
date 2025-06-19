import numpy as np
from ..interfaces import IShortSignal
from ..signal import Signal, Direction

class OrderbookImbalanceSignal(IShortSignal):
    def generate(self, ctx):
        # 예시: bid_vol, ask_vol 각각 float(총합)
        bid_vol = ctx['bid_vol']
        ask_vol = ctx['ask_vol']
        # 매도호가(ask)가 매수호가(bid)보다 1.5배 많을 때 강한 불균형 숏 진입
        if ask_vol > 1.5 * bid_vol:
            score = 1.0
        else:
            score = 0.0

        return Signal("orderbook_imbalance", Direction.SHORT, score)

# ---- 실전/주의/보완 ----
# - bid/ask volume은 실시간 오더북 누적치(최소 3~5단계 합)
# - 기준(1.5배)은 시장/타임프레임마다 다름(실험/백테스트 필수!)
# - 호가 변동 매우 빠름, 단독 신호는 “가짜 신호” 가능성 높음
# - 가격/거래량/캔들패턴/심리 등과 병행 필터링 추천
# - 비정상 체결(특정 대량주문) 대비 필요
