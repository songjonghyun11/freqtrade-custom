# ===== /home/stongone123/freqtrade/src/strategies/entry_signals/__init__.py 시작 =====

# ===== /home/stongone123/freqtrade/src/strategies/entry_signals/__init__.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/entry_signals/alligator_atr.py 시작 =====
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

# ===== /home/stongone123/freqtrade/src/strategies/entry_signals/alligator_atr.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/entry_signals/donchian.py 시작 =====
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

# ===== /home/stongone123/freqtrade/src/strategies/entry_signals/donchian.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/entry_signals/ema_crossover.py 시작 =====
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

# ===== /home/stongone123/freqtrade/src/strategies/entry_signals/ema_crossover.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/entry_signals/rsi_momentum.py 시작 =====
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

# ===== /home/stongone123/freqtrade/src/strategies/entry_signals/rsi_momentum.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/entry_signals/vw_macd.py 시작 =====
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

# ===== /home/stongone123/freqtrade/src/strategies/entry_signals/vw_macd.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/entry_signals/vwap_reversion.py 시작 =====
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

# ===== /home/stongone123/freqtrade/src/strategies/entry_signals/vwap_reversion.py 끝 =====

