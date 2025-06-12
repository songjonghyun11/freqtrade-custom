import requests
import time
import logging
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
from .quality_guard import check_missing

logger = logging.getLogger("collectors.chart_vision")

class ChartVisionCollector(ICollector):
    def fetch(self, ctx):
        start = time.time()
        logger.info("[Collector][chart_vision] 시작")
        try:
            def _api_call(timeout):
                response = requests.post(
                    "https://api.chartvision.example.com/analyze",
                    files={'image': open(ctx.get('chart_path'), 'rb')},
                    timeout=timeout
                )
                if response.status_code != 200:
                    raise Exception(f"비정상 응답: {response.status_code}")
                data = response.json()
                if not data:
                    raise Exception("차트비전 데이터 없음")
                return data

            fallback = ctx.get("prev_vision", {})
            result = fetch_with_retry(_api_call, fallback=fallback)

            if not check_missing(result, ["chart", "timestamp"]):
                logger.warning("[차트비전] 결측 필드/스키마 불일치, fallback 사용: %s", result)
                return fallback

            duration = int((time.time() - start) * 1000)
            logger.info("[Collector][chart_vision] 종료, 수집 1건, 실행시간=%dms", duration)
            return result
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            logger.error("[Collector][chart_vision] 장애 발생: %s, 실행시간=%dms", e, duration)
            return ctx.get("prev_vision", {})
