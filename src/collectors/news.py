import requests
import time
import logging
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
from .models import NewsData
from pydantic import ValidationError
from .quality_guard import check_missing, check_duplicates

logger = logging.getLogger("collectors.news")

class NewsCollector(ICollector):
    def fetch(self, ctx):
        start = time.time()
        logger.info("[Collector][news] 시작")
        try:
            def _api_call(timeout):
                response = requests.get("https://newsapi.example.com/crypto", timeout=timeout)
                if response.status_code != 200:
                    raise Exception(f"비정상 응답: {response.status_code}")
                return response.json().get("articles", [])

            fallback = ctx.get("prev_news", [])
            news_list = fetch_with_retry(_api_call, fallback=fallback)

            valid_news = []
            for n in news_list:
                try:
                    news_obj = NewsData(**n)
                except ValidationError as ve:
                    logger.warning("[뉴스 스키마 결측/불일치] %s", ve)
                    continue
                if not check_missing(n, ["title", "timestamp"]):
                    logger.warning("[뉴스] 결측 필드/스키마 불일치: %s", n)
                    continue
                valid_news.append(news_obj.dict())
            valid_news = check_duplicates(valid_news, ["title", "timestamp"])

            if not valid_news:
                logger.warning("[뉴스] 유효 뉴스 없음, fallback 반환")
                return fallback
            duration = int((time.time() - start) * 1000)
            logger.info("[Collector][news] 종료, 수집=%d, 실행시간=%dms", len(valid_news), duration)
            return valid_news
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            logger.error("[Collector][news] 장애 발생: %s, 실행시간=%dms", e, duration)
            return ctx.get("prev_news", [])
