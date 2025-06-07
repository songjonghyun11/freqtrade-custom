# src/collectors/news.py
import requests
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
import logging

logger = logging.getLogger("collectors.news")

class NewsCollector(ICollector):
    def fetch(self, ctx):
        def _api_call(timeout):
            try:
                response = requests.get("https://newsapi.example.com/crypto", timeout=timeout)
                if response.status_code != 200:
                    raise Exception(f"비정상 응답: {response.status_code}")
                data = response.json().get("articles", [])
                if not data:
                    raise Exception("뉴스 데이터 없음")
                return data
            except Exception as e:
                logger.warning(f"[뉴스 실패] {e}")
                raise

        fallback = ctx.get("prev_news", [])
        if not fallback:
            logger.warning("[뉴스] fallback 값이 None/빈 리스트임")
        try:
            return fetch_with_retry(_api_call, fallback=fallback)
        except Exception as e:
            logger.error(f"[뉴스 최종 실패] fallback도 불가: {e}")
            return fallback
