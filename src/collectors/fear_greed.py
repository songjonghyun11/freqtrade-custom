import requests
import time
import logging
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
from .models import FearGreedData  # 또는 FundingRateData
from pydantic import ValidationError
from .quality_guard import check_missing

logger = logging.getLogger("collectors.fear_greed")  # 또는 funding_rate

class FearGreedCollector(ICollector):
    def fetch(self, ctx):
        start = time.time()
        logger.info("[Collector][fear_greed] 시작")
        try:
            def _api_call(timeout):
                response = requests.get("https://api.feargreed.example.com/index", timeout=timeout)
                if response.status_code != 200:
                    raise Exception(f"비정상 응답: {response.status_code}")
                data = response.json()
                if not data:
                    raise Exception("공포탐욕 데이터 없음")
                return data

            fallback = ctx.get("prev_feargreed", {})
            result = fetch_with_retry(_api_call, fallback=fallback)

            try:
                fg_obj = FearGreedData(**result)
            except ValidationError as ve:
                logger.warning("[공포탐욕 스키마 결측/불일치] %s", ve)
                return fallback

            if not check_missing(fg_obj.dict(), ["value", "value_classification", "timestamp"]):
                logger.warning("[공포탐욕] 결측 필드/스키마 불일치, fallback 사용: %s", result)
                return fallback

            duration = int((time.time() - start) * 1000)
            logger.info("[Collector][fear_greed] 종료, 수집 1건, 실행시간=%dms", duration)
            return fg_obj.dict()
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            logger.error("[Collector][fear_greed] 장애 발생: %s, 실행시간=%dms", e, duration)
            return ctx.get("prev_feargreed", {})
