# src/collectors/fear_greed.py
import requests
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
import logging

logger = logging.getLogger("collectors.fear_greed")

class FearGreedCollector(ICollector):
    def fetch(self, ctx):
        def _api_call(timeout):
            try:
                response = requests.get(
                    "https://api.alternative.me/fng/?limit=1", timeout=timeout
                )
                if response.status_code != 200:
                    raise Exception(f"비정상 응답: {response.status_code}")
                data = response.json()
                if not data or not data.get("data"):
                    raise Exception("공포탐욕 데이터 없음")
                return data["data"][0]
            except Exception as e:
                logger.warning(f"[공포탐욕 실패] {e}")
                raise

        fallback = ctx.get("prev_fg", {})
        if not fallback:
            logger.warning("[공포탐욕] fallback 값이 None/빈 딕셔너리임")
        try:
            return fetch_with_retry(_api_call, fallback=fallback)
        except Exception as e:
            logger.error(f"[공포탐욕 최종 실패] fallback도 불가: {e}")
            return fallback
