# src/collectors/funding_rate.py
import requests
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
import logging

logger = logging.getLogger(__name__)

class FundingRateCollector(ICollector):
    def fetch(self, ctx):
        def _api_call(timeout):
            response = requests.get(
                "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1",
                timeout=timeout
            )
            response.raise_for_status()
            data = response.json()
            return data[0] if isinstance(data, list) and data else data
        fallback_fr = ctx.get("prev_funding_rate", {})
        return fetch_with_retry(_api_call, fallback=fallback_fr)
