# src/collectors/youtube.py
import requests
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
import logging

logger = logging.getLogger("collectors.youtube")

class YoutubeCollector(ICollector):
    def fetch(self, ctx):
        def _api_call(timeout):
            try:
                video_id = ctx.get("video_id", "예시값")
                response = requests.get(
                    f"https://www.googleapis.com/youtube/v3/captions?videoId={video_id}",
                    timeout=timeout
                )
                if response.status_code != 200:
                    raise Exception(f"비정상 응답: {response.status_code}")
                data = response.json()
                if not data:
                    raise Exception("유튜브 캡션 데이터 없음")
                return data
            except Exception as e:
                logger.warning(f"[유튜브 실패] {e}")
                raise

        fallback = ctx.get("prev_caption", {})
        if not fallback:
            logger.warning("[유튜브] fallback 값이 None/빈 딕셔너리임")
        try:
            return fetch_with_retry(_api_call, fallback=fallback)
        except Exception as e:
            logger.error(f"[유튜브 최종 실패] fallback도 불가: {e}")
            return fallback
