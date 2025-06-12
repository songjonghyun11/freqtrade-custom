import requests
import time
import logging
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
from .models import OrderbookData
from pydantic import ValidationError
from .quality_guard import check_missing, check_duplicates

logger = logging.getLogger("collectors.orderbook")

class OrderbookCollector(ICollector):
    def fetch(self, ctx):
        start = time.time()
        logger.info("[Collector][orderbook] 시작")
        try:
            def _api_call(timeout):
                response = requests.get(
                    "https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=5", timeout=timeout
                )
                if response.status_code != 200:
                    raise Exception(f"비정상 응답: {response.status_code}")
                return [response.json()]

            fallback = ctx.get("prev_orderbook", [])
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

            if not valid_obs:
                logger.warning("[오더북] 유효 오더북 없음, fallback 반환")
                return fallback
            duration = int((time.time() - start) * 1000)
            logger.info("[Collector][orderbook] 종료, 수집=%d, 실행시간=%dms", len(valid_obs), duration)
            return valid_obs
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            logger.error("[Collector][orderbook] 장애 발생: %s, 실행시간=%dms", e, duration)
            return ctx.get("prev_orderbook", [])
