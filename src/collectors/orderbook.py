# src/collectors/orderbook.py
import requests
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
from .models import OrderbookData
from pydantic import ValidationError
import logging

logger = logging.getLogger("collectors.orderbook")

class OrderbookCollector(ICollector):
    def fetch(self, ctx):
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
        seen_hash = set()
        for ob in orderbooks:
            try:
                ob_obj = OrderbookData(**ob)
            except ValidationError as ve:
                logger.warning(f"[오더북 스키마 결측/불일치] {ve}")
                continue
            key = f"{ob_obj.symbol}_{ob_obj.timestamp}"
            if key in seen_hash:
                logger.info(f"[오더북 중복 SKIP] {key}")
                continue
            seen_hash.add(key)
            valid_obs.append(ob_obj.dict())

        if not valid_obs:
            logger.warning("[오더북] 유효 오더북 없음, fallback 반환")
            return fallback
        return valid_obs
