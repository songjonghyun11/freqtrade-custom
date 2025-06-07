# src/collectors/fear_greed.py
import requests
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
import logging

logger = logging.getLogger(__name__)

class FearGreedCollector(ICollector):
    def fetch(self, ctx):
        def _api_call(timeout):
            response = requests.get(
                "https://api.alternative.me/fng/?limit=1",
                timeout=timeout
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0] if "data" in data else data
        fallback_fg = ctx.get("prev_fg", {})
        return fetch_with_retry(_api_call, fallback=fallback_fg)
