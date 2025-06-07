# src/collectors/fear_greed.py
import requests
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
from .models import FearGreedData
from pydantic import ValidationError
import logging

logger = logging.getLogger("collectors.fear_greed")

class FearGreedCollector(ICollector):
    def fetch(self, ctx):
        def _api_call(timeout):
            response = requests.get(
                "https://api.alternative.me/fng/?limit=1", timeout=timeout
            )
            if response.status_code != 200:
                raise Exception(f"비정상 응답: {response.status_code}")
            data = response.json()
            return data["data"][0] if "data" in data else data

        fallback = ctx.get("prev_fg", {})
        fg = fetch_with_retry(_api_call, fallback=fallback)

        try:
            fg_obj = FearGreedData(**fg)
        except ValidationError as ve:
            logger.warning(f"[공포탐욕 스키마 결측/불일치] {ve}")
            return fallback

        return fg_obj.dict()
