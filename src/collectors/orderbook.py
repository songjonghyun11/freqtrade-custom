import requests, time, logging, os, json
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
from .models import OrderbookData
from pydantic import ValidationError
from .quality_guard import check_missing, check_duplicates
from datetime import datetime

logger = logging.getLogger("collectors.orderbook")

def save_collector_data(symbol, collector_name, data):
    folder = f"data/{symbol}"; os.makedirs(folder, exist_ok=True)
    with open(f"{folder}/{collector_name}.json", "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.utcnow().isoformat(), "data": data}, ensure_ascii=False) + "\n")
    backup_dir = "backup"; os.makedirs(backup_dir, exist_ok=True)
    with open(f"{backup_dir}/{symbol}_{collector_name}_{datetime.utcnow().strftime('%Y%m%d')}.bak", "a", encoding="utf-8") as bakf:
        bakf.write(json.dumps({"ts": datetime.utcnow().isoformat(), "data": data}, ensure_ascii=False) + "\n")

def write_log(symbol, collector_name, message):
    log_path = f"logs/{symbol}.log"
    with open(log_path, "a", encoding="utf-8") as logf:
        logf.write(f"[{datetime.utcnow().isoformat()}][{collector_name}] {message}\n")

class OrderbookCollector(ICollector):
    def fetch(self, ctx):
        start = time.time(); symbol = ctx.get("symbol", "UNKNOWN")
        logger.info("[Collector][orderbook] 시작")
        try:
            def _api_call(timeout):
                response = requests.get("https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=5", timeout=timeout)
                if response.status_code != 200: raise Exception(f"비정상 응답: {response.status_code}")
                return [response.json()]

            fallback = ctx.get("prev_orderbook", [{
                "symbol": symbol,
                "bids": [["100.0", "1.0"]],
                "asks": [["101.0", "1.5"]],
                "timestamp": int(time.time())
            }])

            orderbooks = fetch_with_retry(_api_call, fallback=fallback)
            valid_obs = []
            for ob in orderbooks:
                try:
                    ob_obj = OrderbookData(**ob)
                except ValidationError as ve:
                    logger.warning("[오더북 스키마 결측/불일치] %s", ve)
                    continue
                if not check_missing(ob, ["symbol", "bids", "asks", "timestamp"]):
                    logger.warning("[오더북] 결측 필드/스키마 불일치: %s", ob)
                    continue
                valid_obs.append(ob_obj.dict())
            valid_obs = check_duplicates(valid_obs, ["symbol", "timestamp"])

            save_collector_data(symbol, "orderbook", valid_obs)
            if not valid_obs:
                write_log(symbol, "orderbook", "수집 데이터 없음/이상치")
                logger.warning("[오더북] 유효 오더북 없음, fallback 반환")
                return fallback
            duration = int((time.time() - start) * 1000)
            logger.info("[Collector][orderbook] 종료, 수집=%d, 실행시간=%dms", len(valid_obs), duration)
            write_log(symbol, "orderbook", f"수집 정상 | 건수: {len(valid_obs)}")
            return valid_obs
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            logger.error("[Collector][orderbook] 장애 발생: %s, 실행시간=%dms", e, duration)
            write_log(symbol, "orderbook", f"오더북 수집 장애: {str(e)}")
            save_collector_data(symbol, "orderbook_error", {"error": str(e), "ts": datetime.utcnow().isoformat()})
            return {
                "symbol": symbol,
                "bids": [["100.0", "1.0"]],
                "asks": [["101.0", "1.5"]],
                "timestamp": int(time.time())
            }

def fetch_orderbook(symbol: str):
    return OrderbookCollector().fetch({"symbol": symbol})
