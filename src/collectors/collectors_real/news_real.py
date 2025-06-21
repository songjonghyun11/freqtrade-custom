import requests
import time
import logging
import os
import json
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
from .models import NewsData
from pydantic import ValidationError
from .quality_guard import check_missing, check_duplicates
from datetime import datetime

def save_collector_data(symbol, collector_name, data):
    folder = f"data/{symbol}"
    os.makedirs(folder, exist_ok=True)
    save_path = f"{folder}/{collector_name}.json"
    with open(save_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.utcnow().isoformat(), "data": data}, ensure_ascii=False) + "\n")

    backup_dir = "backup"
    os.makedirs(backup_dir, exist_ok=True)
    backup_path = f"{backup_dir}/{symbol}_{collector_name}_{datetime.utcnow().strftime('%Y%m%d')}.bak"
    with open(backup_path, "a", encoding="utf-8") as bakf:
        bakf.write(json.dumps({"ts": datetime.utcnow().isoformat(), "data": data}, ensure_ascii=False) + "\n")

def write_log(symbol, collector_name, message):
    log_path = f"logs/{symbol}.log"
    with open(log_path, "a", encoding="utf-8") as logf:
        logf.write(f"[{datetime.utcnow().isoformat()}][{collector_name}] {message}\n")

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

            symbol = ctx.get("symbol", "UNKNOWN")

            if not valid_news:
                write_log(symbol, "news", "유효 뉴스 없음/이상치")
                logger.warning("[뉴스] 유효 뉴스 없음, fallback 반환")
            # 실패도 로그/백업 남김
                save_collector_data(symbol, "news_error", {"error": "no_valid_news", "ts": datetime.utcnow().isoformat()})
                return fallback

            # 수집 성공시 데이터 저장/로그
            save_collector_data(symbol, "news", valid_news)
            write_log(symbol, "news", f"뉴스 수집 성공 | 건수: {len(valid_news)}")

            duration = int((time.time() - start) * 1000)
            logger.info("[Collector][news] 종료, 수집=%d, 실행시간=%dms", len(valid_news), duration)
            return valid_news
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            logger.error("[Collector][news] 장애 발생: %s, 실행시간=%dms", e, duration)
            symbol = ctx.get("symbol", "UNKNOWN")
            write_log(symbol, "news", f"뉴스 수집 장애: {str(e)}")
            save_collector_data(symbol, "news_error", {"error": str(e), "ts": datetime.utcnow().isoformat()})
            return ctx.get("prev_news", [])
        
def fetch_news(symbol: str):
    collector = NewsCollector()
    return collector.fetch({"symbol": symbol})