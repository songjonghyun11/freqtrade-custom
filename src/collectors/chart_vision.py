# src/collectors/chart_vision.py
import requests
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
import logging

logger = logging.getLogger("collectors.chart_vision")

class ChartVisionCollector(ICollector):
    def fetch(self, ctx):
        def _api_call(timeout):
            try:
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
            except Exception as e:
                logger.warning(f"[차트비전 실패] {e}")
                raise

        fallback = ctx.get("prev_vision", {})
        if not fallback:
            logger.warning("[차트비전] fallback 값이 None/빈 딕셔너리임")
        try:
            return fetch_with_retry(_api_call, fallback=fallback)
        except Exception as e:
            logger.error(f"[차트비전 최종 실패] fallback도 불가: {e}")
            return fallback
