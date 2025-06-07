# src/collectors/chart_vision.py
import requests
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
import logging

logger = logging.getLogger(__name__)

class ChartVisionCollector(ICollector):
    def fetch(self, ctx):
        def _api_call(timeout):
            # 실제론 차트 이미지 업로드/GPT Vision 호출 등으로 변경!
            response = requests.post(
                "https://api.chartvision.example.com/analyze",
                files={'image': open(ctx.get('chart_path'), 'rb')},
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        fallback_vision = ctx.get("prev_vision", {})
        return fetch_with_retry(_api_call, fallback=fallback_vision)
