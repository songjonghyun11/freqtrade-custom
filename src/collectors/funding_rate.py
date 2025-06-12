import requests
import logging
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
from .models import FundingRateData
from pydantic import ValidationError
from .quality_guard import check_missing

logger = logging.getLogger("collectors.funding_rate")

class FundingRateCollector(ICollector):
    def fetch(self, ctx):
        logger.info("[Collector][funding_rate] 시작")
        try:
            def _api_call(timeout):
                response = requests.get("https://api.fundingrate.example.com/latest", timeout=timeout)
                if response.status_code != 200:
                    raise Exception(f"비정상 응답: {response.status_code}")
                data = response.json()
                if not data:
                    raise Exception("펀딩비 데이터 없음")
                return data

            fallback = ctx.get("prev_funding_rate", {})
            result = fetch_with_retry(_api_call, fallback=fallback)

            try:
                fr_obj = FundingRateData(**result)
            except ValidationError as ve:
                logger.warning("[펀딩비 스키마 결측/불일치] %s", ve)
                return fallback

            if not check_missing(fr_obj.dict(), ["symbol", "rate", "timestamp"]):
                logger.warning("[펀딩비] 결측 필드/스키마 불일치, fallback 사용: %s", result)
                return fallback

            logger.info("[Collector][funding_rate] 종료, 수집 1건")
            return fr_obj.dict()
        except Exception as e:
            logger.error("[Collector][funding_rate] 장애 발생: %s", e)
            return ctx.get("prev_funding_rate", {})
