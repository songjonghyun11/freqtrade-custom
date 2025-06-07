# src/collectors/youtube.py
import requests
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
import logging

logger = logging.getLogger(__name__)

class YoutubeCollector(ICollector):
    def fetch(self, ctx):
        def _api_call(timeout):
            # 실제론 YouTube Data API로 교체!
            video_id = ctx.get("video_id", "예시값")
            response = requests.get(
                f"https://www.googleapis.com/youtube/v3/captions?videoId={video_id}",
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        fallback_caption = ctx.get("prev_caption", {})
        return fetch_with_retry(_api_call, fallback=fallback_caption)
