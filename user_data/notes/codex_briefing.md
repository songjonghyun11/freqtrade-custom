# Codex 브리핑 - TestDonchianFearGreedStrategy

## 1. 환경 / 실행 전제

- OS: WSL(Ubuntu) on Windows
- 프로젝트 루트: ~/freqtrade
- Freqtrade 실행 방식: Docker
  - 이미지: freqtradeorg/freqtrade:stable
  - user_data 마운트: -v "$(pwd)/user_data:/freqtrade/user_data"

## 2. 전략 개요

- 전략명 / 클래스명 / 파일명:
  - TestDonchianFearGreedStrategy
  - user_data/strategies/TestDonchianFearGreedStrategy.py
- 메인 아이디어:
  - ENTRY: Donchian 돌파 + 거래량 필터 + Fear & Greed (FG) 지수
  - EXIT:
    - ROI 최소 수익
    - 고정 stoploss (-1%)
    - 트레일링 스탑
    - 커스텀 청산 신호: ema_cross_exit (EMA 교차 기반 청산)

## 3. 현재 ENTRY / EXIT 세팅 (중요)

### ENTRY (단일 소스화 완료)

- ENTRY 파라미터는 오직 여기에서만 읽는다:
  - user_data/config/config_spot.json
  - strategy_parameters.TestDonchianFearGreedStrategyFG

- 현재 값:
  - buy_dc_period = 19
  - buy_fg_threshold = 52
  - buy_vol_mult = 3.5
  - use_fg = 1
  - use_trend_filter = 1   # EMA200 레짐 필터 ON
  - trend_ema_period = 200

- _entry_param(key, cast, default=None, **kwargs) 헬퍼로 읽고,
  다른 곳(flat config, Parameter.value 등)은 무시한다.

### EXIT (기준선)

- override 파일: user_data/overrides/exit_baseline.json
- 내용 요약:
  - use_exit_signal = true
  - exit_profit_only = false
  - ignore_roi_if_entry_signal = false
  - minimal_roi: {0: 0.006, 10: 0.0035, 30: 0.0}
  - stoploss = -0.01
  - trailing_stop = true
  - trailing_stop_positive = 0.002
  - trailing_stop_positive_offset = 0.003
  - trailing_only_offset_is_reached = true

### 커스텀 EXIT: ema_cross_exit

- 파일: user_data/strategies/ema_cross_exit.py
- 역할:
  - EMA 교차(단기/장기)로 추세 종료를 감지해서 청산 신호 생성
  - TestDonchianFearGreedStrategy에서 이 모듈을 import 해서 사용

## 4. 최근 백테스트 결과 (기준선 + EMA200 ON, BACK 구간)

- 타임레인지: BACK = 20250926-20251106
- 결과 (EMA200 레짐 필터 ON):
  - Trades: 183
  - Total profit %: -3.87%
  - Avg profit %: -0.21%
  - Avg duration: 0:24:00
  - Drawdown: 39.362 USDT (3.93%)

- exit_reason 개수 요약:
  - roi: 83
  - ema_cross_exit: 47
  - trailing_stop_loss: 29
  - stop_loss: 24

- 최악 10개 트레이드 특징:
  - 전부 exit_reason = stop_loss
  - 손실: 약 -1.2 USDT (stake 100 기준 약 -1%+수수료)
  - 코인: SOL/LINK/LTC/AVAX
  - 동일 타임스탬프에 여러 코인이 같이 맞는 경우가 있음 (시장 급락 구간)

## 5. Codex에게 부탁할 작업 방향 (원칙)

- 한 번에 "작은 단위"만 수정:
  - 예: ema_cross_exit 내부 로직 개선 1개,
  - 또는 ENTRY 필터 조건 1개 등.
- 수정 대상 파일:
  - user_data/strategies/TestDonchianFearGreedStrategy.py
  - user_data/strategies/ema_cross_exit.py
  - user_data/config/config_spot.json
  - user_data/overrides/*.json (exit_baseline 등)

- 수정 후 반드시 할 것:
  1) python -m py_compile <수정된 .py 파일들>
  2) Docker backtesting 1회 실행
     - BACK 구간: 20250926-20251106
     - 명령 예시는 내가 별도로 제공할 예정.

- 금지 사항:
  - config_spot.json에 ENTRY 관련 flat 키를 다시 추가하지 말 것
    (buy_dc_period, buy_fg_threshold, buy_vol_mult, use_fg 등)
  - 새로운 전략 파일을 만들 때는 반드시 나와 상의하고 시작할 것.
