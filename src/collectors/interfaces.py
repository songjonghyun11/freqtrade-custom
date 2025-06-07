# src/collectors/orderbook.py
import requests
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
import logging

logger = logging.getLogger(__name__)

class OrderbookCollector(ICollector):
    def fetch(self, ctx):
        def _api_call(timeout):
            response = requests.get("https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=5", timeout=timeout)
            response.raise_for_status()
            return response.json()

        fallback_orderbook = ctx.get("prev_orderbook", {})
        return fetch_with_retry(_api_call, fallback=fallback_orderbook)
