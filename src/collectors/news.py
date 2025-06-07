# src/collectors/news.py
import requests
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
from .models import NewsData
from pydantic import ValidationError
import logging

logger = logging.getLogger("collectors.news")

class NewsCollector(ICollector):
    def fetch(self, ctx):
        def _api_call(timeout):
            response = requests.get("https://newsapi.example.com/crypto", timeout=timeout)
            if response.status_code != 200:
                raise Exception(f"비정상 응답: {response.status_code}")
            return response.json().get("articles", [])

        fallback = ctx.get("prev_news", [])
        news_list = fetch_with_retry(_api_call, fallback=fallback)

        valid_news = []
        seen_hash = set()
        for n in news_list:
            try:
                news_obj = NewsData(**n)
            except ValidationError as ve:
                logger.warning(f"[뉴스 스키마 결측/불일치] {ve}")
                continue
            key = f"{news_obj.title}_{news_obj.timestamp}"
            if key in seen_hash:
                logger.info(f"[뉴스 중복 SKIP] {key}")
                continue
            seen_hash.add(key)
            valid_news.append(news_obj.dict())

        if not valid_news:
            logger.warning("[뉴스] 유효 뉴스 없음, fallback 반환")
            return fallback
        return valid_news
