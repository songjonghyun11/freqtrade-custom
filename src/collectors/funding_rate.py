# src/collectors/funding_rate.py
import requests
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
import logging

logger = logging.getLogger("collectors.funding_rate")

class FundingRateCollector(ICollector):
    def fetch(self, ctx):
        def _api_call(timeout):
            try:
                response = requests.get(
                    "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1", timeout=timeout
                )
                if response.status_code != 200:
                    raise Exception(f"비정상 응답: {response.status_code}")
                data = response.json()
                if not data:
                    raise Exception("펀딩비 데이터 없음")
                return data[0] if isinstance(data, list) and data else data
            except Exception as e:
                logger.warning(f"[펀딩비 실패] {e}")
                raise

        fallback = ctx.get("prev_funding_rate", {})
        if not fallback:
            logger.warning("[펀딩비] fallback 값이 None/빈 딕셔너리임")
        try:
            return fetch_with_retry(_api_call, fallback=fallback)
        except Exception as e:
            logger.error(f"[펀딩비 최종 실패] fallback도 불가: {e}")
            return fallback
