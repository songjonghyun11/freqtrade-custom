# src/collectors/social_media.py
import requests
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
from .models import SocialMediaTrend
from pydantic import ValidationError
import logging

logger = logging.getLogger("collectors.social_media")

class SocialMediaCollector(ICollector):
    def fetch(self, ctx):
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
        seen_hash = set()
        for t in trends:
            try:
                trend_obj = SocialMediaTrend(**t)
            except ValidationError as ve:
                logger.warning(f"[소셜미디어 스키마 결측/불일치] {ve}")
                continue
            key = f"{trend_obj.keyword}_{trend_obj.timestamp}"
            if key in seen_hash:
                logger.info(f"[트렌드 중복 SKIP] {key}")
                continue
            seen_hash.add(key)
            valid_trends.append(trend_obj.dict())

        if not valid_trends:
            logger.warning("[소셜미디어] 유효 트렌드 없음, fallback 반환")
            return fallback
        return valid_trends
