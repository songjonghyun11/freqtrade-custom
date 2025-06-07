# src/collectors/social_media.py
import requests
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
import logging

logger = logging.getLogger(__name__)

class SocialMediaCollector(ICollector):
    def fetch(self, ctx):
        def _api_call(timeout):
            # 예: 트위터 트렌드 API. 실제 엔드포인트로 교체
            response = requests.get(
                "https://api.socialmedia.example.com/trends?keyword=bitcoin",
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        fallback_trends = ctx.get("prev_trends", [])
        return fetch_with_retry(_api_call, fallback=fallback_trends)
