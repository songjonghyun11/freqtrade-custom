# quick_check_collectors.py
# 모든 collector를 한 번에 스모크 테스트합니다.
# 데이터가 없으면 각 collector가 가진 기본/FFILL 로직으로 안전하게 동작해야 합니다.

import os
from pprint import pprint

# --- imports: 현재 폴더의 모듈들 ---
from fear_greed import FearGreedCollector
from funding_rate import FundingRateCollector
from orderbook import OrderbookCollector
from chart_vision import ChartVisionCollector
from news import NewsCollector
from ohlcv_collector import OHLCVCollector
from data_source import SampleDataSource  # 샘플 OHLCV 소스
try:
    # 선택: 품질 로그/디렉토리 생성 확인
    from quality_guard import write_quality_log
except Exception:
    write_quality_log = None

SYMBOL = "BTC_USDT"
TS = 1704067200           # 예시 타임스탬프(2023-12-31 00:00 UTC 근처). 데이터에 없는 경우 FFILL/기본값 사용.
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def hr(title: str):
    print("\n" + "=" * 12 + f" {title} " + "=" * 12)

def test_fear_greed():
    hr("FearGreedCollector")
    c = FearGreedCollector(mode="backtest", data_dir=DATA_DIR)
    res = c.fetch(SYMBOL, TS)
    pprint(res)

def test_funding_rate():
    hr("FundingRateCollector")
    c = FundingRateCollector(mode="backtest", data_dir=DATA_DIR)
    res = c.fetch(SYMBOL, TS)
    pprint(res)

def test_orderbook():
    hr("OrderbookCollector")
    c = OrderbookCollector(mode="backtest", data_dir=DATA_DIR)
    res = c.fetch(SYMBOL, TS)
    # 핵심 요약만 표시
    slim = {
        "symbol": res.get("symbol"),
        "timestamp": res.get("timestamp"),
        "imbalance": res.get("imbalance"),
        "bids_len": len(res.get("bids", [])),
        "asks_len": len(res.get("asks", [])),
    }
    pprint(slim)

def test_chart_vision():
    hr("ChartVisionCollector")
    c = ChartVisionCollector(mode="backtest", data_dir=DATA_DIR)
    res = c.fetch(SYMBOL, TS)
    pprint(res)

def test_news():
    hr("NewsCollector")
    c = NewsCollector(data_dir=DATA_DIR)
    arr = c.fetch_news(SYMBOL, TS)
    print(f"items: {len(arr)}")
    pprint(arr[:2])  # 많으면 2개만 미리보기

def test_ohlcv():
    hr("OHLCVCollector (with SampleDataSource)")
    src = SampleDataSource()
    oc = OHLCVCollector(data_source=src)
    df = oc.fetch(SYMBOL, timeframe="5m")
    print("shape:", df.shape)
    print(df.tail(3))

def test_quality_log():
    if write_quality_log is None:
        return
    hr("quality_guard.write_quality_log")
    try:
        write_quality_log(SYMBOL, "smoke", "collector quick check runs")
        print("logs/ 디렉토리 및 로그 파일 생성 OK")
    except Exception as e:
        print("quality_guard 로그 생성 실패:", e)

def main():
    print(f"[SMOKE] symbol={SYMBOL}, ts={TS}, data_dir={DATA_DIR}")
    # 개별 테스트 실행
    test_fear_greed()
    test_funding_rate()
    test_orderbook()
    test_chart_vision()
    test_news()
    test_ohlcv()
    test_quality_log()
    print("\n[SMOKE DONE] 모든 collector 스모크 테스트 완료")

if __name__ == "__main__":
    main()
