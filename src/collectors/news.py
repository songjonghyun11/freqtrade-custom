# src/collectors/news.py
import requests
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
import logging

logger = logging.getLogger(__name__)

class NewsCollector(ICollector):
    def fetch(self, ctx):
        def _api_call(timeout):
            # 실제론 여기에 news API 엔드포인트!
            response = requests.get("https://newsapi.example.com/crypto", timeout=timeout)
            response.raise_for_status()
            return response.json()["articles"]  # 데이터 포맷에 맞게 수정

        # fallback: 직전 뉴스(없으면 빈 리스트)
        fallback_news = ctx.get("prev_news", [])
        return fetch_with_retry(_api_call, fallback=fallback_news)
