import numpy as np
import talib
from ..interfaces import IEntrySignal
from ..signal import Signal, Direction

class AlligatorATRSignal(IEntrySignal):
    def generate(self, ctx):
        close = ctx['close']  # np.array, 길이 30 이상 추천
        high = ctx['high']
        low = ctx['low']

        # === Alligator(EMA 13/8/5)
        jaw = talib.EMA(close, timeperiod=13)[-1]    # 턱
        teeth = talib.EMA(close, timeperiod=8)[-1]   # 이빨
        lips = talib.EMA(close, timeperiod=5)[-1]    # 입술

        # === ATR(14): 변동성 체크
        atr = talib.ATR(high, low, close, timeperiod=14)[-1]

        # === 진입조건 ===
        # 1) 상승배열(입술 > 이빨 > 턱)
        # 2) 종가가 턱(EMA13) 위
        # 3) ATR 0.01 이상(=시장에 변동성 충분)
        if lips > teeth > jaw and close[-1] > jaw and atr > 0.01:
            score = 1.0
        else:
            score = 0.0

        return Signal("alligator_atr", Direction.LONG, score)

# ---- 실전/주의/보완 ----
# - 반드시 np.array 타입으로 입력 (list/Series 안 됨)
# - TA-Lib 미설치시 오류! (pip install ta-lib + so파일 필요)
# - 13/8/5, ATR 14는 기본값 → 하이퍼옵트로 꼭 튜닝 추천
# - 변동성 적은 장, 횡보장에선 “가짜 신호”에 주의 (ATR 기준 조절)
# - EMA와 SMA 섞지 말 것! (일관성 필수)
# - ATR 임계치(0.01)는 코인/시장/타임프레임에 맞게 보정
