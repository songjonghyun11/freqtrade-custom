# src/collectors/funding_rate.py
import requests
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
from .models import FundingRateData
from pydantic import ValidationError
import logging

logger = logging.getLogger("collectors.funding_rate")

class FundingRateCollector(ICollector):
    def fetch(self, ctx):
        def _api_call(timeout):
            response = requests.get(
                "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1", timeout=timeout
            )
            if response.status_code != 200:
                raise Exception(f"비정상 응답: {response.status_code}")
            data = response.json()
            return data[0] if isinstance(data, list) and data else data

        fallback = ctx.get("prev_funding_rate", {})
        funding = fetch_with_retry(_api_call, fallback=fallback)

        try:
            funding_obj = FundingRateData(**funding)
        except ValidationError as ve:
            logger.warning(f"[펀딩비 스키마 결측/불일치] {ve}")
            return fallback

        return funding_obj.dict()
