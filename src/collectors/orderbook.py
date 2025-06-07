# src/collectors/orderbook.py
import requests
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
import logging

logger = logging.getLogger("collectors.orderbook")

class OrderbookCollector(ICollector):
    def fetch(self, ctx):
        def _api_call(timeout):
            try:
                response = requests.get(
                    "https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=5", timeout=timeout
                )
                if response.status_code != 200:
                    raise Exception(f"비정상 응답: {response.status_code}")
                data = response.json()
                if not data or "bids" not in data:
                    raise Exception("오더북 데이터 없음")
                return data
            except Exception as e:
                logger.warning(f"[오더북 실패] {e}")
                raise

        fallback = ctx.get("prev_orderbook", {})
        if not fallback:
            logger.warning("[오더북] fallback 값이 None/빈 딕셔너리임")
        try:
            return fetch_with_retry(_api_call, fallback=fallback)
        except Exception as e:
            logger.error(f"[오더북 최종 실패] fallback도 불가: {e}")
            return fallback
