import talib
from ..interfaces import IShortSignal
from ..signal import Signal, Direction

class BBReversionSignal(IShortSignal):
    def generate(self, ctx):
        close = ctx['close']
        # 볼린저밴드(20, 2.0): 업계 표준
        upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
        
        # 종가가 밴드 상단 돌파 후 복귀(=반전 숏 진입)
        if close[-1] > upper[-1]:
            score = 1.0
        else:
            score = 0.0

        return Signal("bb_reversion", Direction.SHORT, score)

# ---- 실전/주의/보완 ----
# - 볼린저밴드 파라미터(20, 2)는 기본값, 시장별 실험 필수!
# - 추세장에선 “상단 돌파 후 더 폭등”하는 경우 많음(단순 진입은 위험)
# - 반드시 “돌파→복귀 패턴”/캔들형/거래량 등 보조 필터 권장
# - 밴드폭이 좁아지면 ‘급등락’ 신호 가능성 높음(=돌파+트렌드 주의!)
