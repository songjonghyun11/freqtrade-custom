import requests
import time
import logging
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
from .quality_guard import check_missing

logger = logging.getLogger("collectors.youtube")

class YoutubeCollector(ICollector):
    def fetch(self, ctx):
        start = time.time()
        logger.info("[Collector][youtube] 시작")
        try:
            def _api_call(timeout):
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

            fallback = ctx.get("prev_caption", {})
            result = fetch_with_retry(_api_call, fallback=fallback)

            if not check_missing(result, ["caption", "timestamp"]):
                logger.warning("[유튜브] 결측 필드/스키마 불일치, fallback 사용: %s", result)
                return fallback

            duration = int((time.time() - start) * 1000)
            logger.info("[Collector][youtube] 종료, 수집 1건, 실행시간=%dms", duration)
            return result
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            logger.error("[Collector][youtube] 장애 발생: %s, 실행시간=%dms", e, duration)
            return ctx.get("prev_caption", {})
