import talib
import numpy as np
from ..interfaces import IEntrySignal
from ..signal import Signal, Direction

class VWMacdSignal(IEntrySignal):
    def generate(self, ctx):
        close = ctx['close']
        volume = ctx.get('volume', np.ones_like(close))

        macd, macdsignal, _ = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        vwap = np.sum(close[-20:] * volume[-20:]) / np.sum(volume[-20:])  # 20봉 기준

        # MACD > Signal, 종가가 VWAP 위 = 강세 전환
        if macd[-1] > macdsignal[-1] and close[-1] > vwap:
            score = 1.0
        else:
            score = 0.0

        return Signal("vw_macd", Direction.LONG, score)

# ---- 실전/주의/보완 ----
# - MACD 파라미터(12/26/9)는 기본값, 자산/타임프레임별 실험 추천
# - VWAP(20봉)은 시장에 따라 확장 가능(예: 일봉/5분봉)
# - 볼륨 데이터 누락시 np.ones로 대체(실전은 반드시 실제 거래량 넣을 것!)
# - MACD 신호+VWAP 조합은 “추세장”에서 가장 효과적, 횡보장엔 오히려 약함
# - 신호 겹침/오버트레이딩 위험성 주의
