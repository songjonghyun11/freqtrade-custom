# src/collectors/social_media.py
import requests
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
import logging

logger = logging.getLogger("collectors.social_media")

class SocialMediaCollector(ICollector):
    def fetch(self, ctx):
        def _api_call(timeout):
            try:
                response = requests.get(
                    "https://api.socialmedia.example.com/trends?keyword=bitcoin", timeout=timeout
                )
                if response.status_code != 200:
                    raise Exception(f"비정상 응답: {response.status_code}")
                data = response.json()
                if not data:
                    raise Exception("소셜미디어 트렌드 데이터 없음")
                return data
            except Exception as e:
                logger.warning(f"[소셜미디어 실패] {e}")
                raise

        fallback = ctx.get("prev_trends", [])
        if not fallback:
            logger.warning("[소셜미디어] fallback 값이 None/빈 리스트임")
        try:
            return fetch_with_retry(_api_call, fallback=fallback)
        except Exception as e:
            logger.error(f"[소셜미디어 최종 실패] fallback도 불가: {e}")
            return fallback
