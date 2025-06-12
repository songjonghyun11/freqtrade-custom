import requests
import time
import logging
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
from .models import SocialMediaTrend
from pydantic import ValidationError
from .quality_guard import check_missing, check_duplicates

logger = logging.getLogger("collectors.social_media")

class SocialMediaCollector(ICollector):
    def fetch(self, ctx):
        start = time.time()
        logger.info("[Collector][social_media] 시작")
        try:
            def _api_call(timeout):
                response = requests.get(
                    "https://api.socialmedia.example.com/trends?keyword=bitcoin", timeout=timeout
                )
                if response.status_code != 200:
                    raise Exception(f"비정상 응답: {response.status_code}")
                return response.json().get("trends", [])

            fallback = ctx.get("prev_trends", [])
            trends = fetch_with_retry(_api_call, fallback=fallback)

            valid_trends = []
            for t in trends:
                try:
                    trend_obj = SocialMediaTrend(**t)
                except ValidationError as ve:
                    logger.warning("[소셜미디어 스키마 결측/불일치] %s", ve)
                    continue
                if not check_missing(t, ["keyword", "score", "timestamp"]):
                    logger.warning("[소셜미디어] 결측 필드/스키마 불일치: %s", t)
                    continue
                valid_trends.append(trend_obj.dict())
            valid_trends = check_duplicates(valid_trends, ["keyword", "timestamp"])

            if not valid_trends:
                logger.warning("[소셜미디어] 유효 트렌드 없음, fallback 반환")
                return fallback
            duration = int((time.time() - start) * 1000)
            logger.info("[Collector][social_media] 종료, 수집=%d, 실행시간=%dms", len(valid_trends), duration)
            return valid_trends
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            logger.error("[Collector][social_media] 장애 발생: %s, 실행시간=%dms", e, duration)
            return ctx.get("prev_trends", [])
