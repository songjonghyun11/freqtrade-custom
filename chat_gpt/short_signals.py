# ===== /home/stongone123/freqtrade/src/strategies/short_signals/__init__.py 시작 =====

# ===== /home/stongone123/freqtrade/src/strategies/short_signals/__init__.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/short_signals/sample_short.py 시작 =====
from ..interfaces import IShortSignal
from ..signal import Signal, Direction

class SampleShort(IShortSignal):
    def generate(self, ctx) -> Signal:
        # TODO: 실제 숏 진입 로직
        return Signal("SampleShort", Direction.SHORT, 0.0)

# ===== /home/stongone123/freqtrade/src/strategies/short_signals/sample_short.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/short_signals/rsi_overbought.py 시작 =====
import talib
from ..interfaces import IShortSignal
from ..signal import Signal, Direction

class RSIOverboughtSignal(IShortSignal):
    def generate(self, ctx):
        close = ctx['close']
        rsi = talib.RSI(close, timeperiod=14)[-1]

        # RSI 70 초과면 과매수→반전 숏 진입
        if rsi > 70:
            score = 1.0
        else:
            score = 0.0

        return Signal("rsi_overbought", Direction.SHORT, score)

# ---- 실전/주의/보완 ----
# - RSI(14)는 업계 표준, 과매수 기준(70)은 시장상황 따라 조정(60~80)
# - 과매수 지속 구간(‘역추세 장세’)에선 손실 위험 높음(추세장에선 오히려 매수세 폭등 가능!)
# - “반전+추세” 신호와 반드시 병행 실험 추천
# - 데이터 길이(최소 20~30) 미만이면 신호 불안정
# - 단독보단 볼린저밴드/모멘텀/거래량 등 보조 필터와 조합 추천

# ===== /home/stongone123/freqtrade/src/strategies/short_signals/rsi_overbought.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/short_signals/bb_reversion.py 시작 =====
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

# ===== /home/stongone123/freqtrade/src/strategies/short_signals/bb_reversion.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/short_signals/funding_rate.py 시작 =====
from ..interfaces import IShortSignal
from ..signal import Signal, Direction

class FundingRateSignal(IShortSignal):
    def generate(self, ctx):
        funding = ctx['funding']  # 실전: 최근 펀딩비(%), float
        # 기준값: 0.05% 이상이면 비정상(롱 쏠림)→역추세 숏 진입
        if funding > 0.0005:
            score = 1.0
        else:
            score = 0.0

        return Signal("funding_rate", Direction.SHORT, score)

# ---- 실전/주의/보완 ----
# - funding은 실제 거래소에서 주기별 받아와야 함(FTX, Binance, Bybit 등)
# - 기준치(0.05%)는 시장/코인별 차이 큼(역전/급등 전 데이터 필수 분석)
# - “롱 쏠림”에만 숏, “숏 쏠림”엔 반대 신호(매수)도 확장 가능
# - 단독 신호 위험, 오더북/심리/가격패턴 등과 반드시 병행 실험
# - 극단적 펀딩 뒤엔 반대 급등락도 잦음(시장 패닉 주의!)

# ===== /home/stongone123/freqtrade/src/strategies/short_signals/funding_rate.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/short_signals/orderbook_imbalance.py 시작 =====
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

# ===== /home/stongone123/freqtrade/src/strategies/short_signals/orderbook_imbalance.py 끝 =====

# ===== /home/stongone123/freqtrade/src/strategies/short_signals/momentum_divergence.py 시작 =====
import talib
from ..interfaces import IShortSignal
from ..signal import Signal, Direction

class MomentumDivergenceSignal(IShortSignal):
    def generate(self, ctx):
        close = ctx['close']
        macd, macdsignal, _ = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)

        # 가격은 신고가, MACD는 저점(다이버전스) 발생 시 반전 숏 신호
        if close[-1] > max(close[-10:-1]) and macd[-1] < macd[-2]:
            score = 1.0
        else:
            score = 0.0

        return Signal("momentum_divergence", Direction.SHORT, score)

# ---- 실전/주의/보완 ----
# - “가격은 고점 돌파, 모멘텀(MACD)은 약화” → 다이버전스 전형적 신호
# - 구간(10봉)·모멘텀지표(MACD/RSI 등) 실험으로 최적화 추천
# - 단독 신호는 “상승장/펌핑장”에선 위협, 필터 조합(거래량/캔들) 필요
# - 신호 연속 발생 시 “중복 진입/과매매” 주의!
# - 조건 단순화 → 실제론 구간/지표 더 세분화해 실험

# ===== /home/stongone123/freqtrade/src/strategies/short_signals/momentum_divergence.py 끝 =====

