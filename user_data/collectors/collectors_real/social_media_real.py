import requests
import time
import logging
import os
import json
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
from .models import SocialMediaTrend
from pydantic import ValidationError
from .quality_guard import check_missing, check_duplicates
from datetime import datetime

logger = logging.getLogger("collectors.social_media")

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

class SocialMediaCollector(ICollector):
    def fetch(self, ctx):
        start = time.time()
        symbol = ctx.get("symbol", "UNKNOWN")
        logger.info("[Collector][social_media] 시작")
        try:
            def _api_call(timeout):
                response = requests.get(
                    "https://api.socialmedia.example.com/trends?keyword=bitcoin", timeout=timeout
                )
                if response.status_code != 200:
                    raise Exception(f"비정상 응답: {response.status_code}")
                return response.json().get("trends", [])

            fallback = ctx.get("prev_trends", [])
            trends = fetch_with_retry(_api_call, fallback=fallback)

            valid_trends = []
            for t in trends:
                try:
                    trend_obj = SocialMediaTrend(**t)
                except ValidationError as ve:
                    logger.warning("[소셜미디어 스키마 결측/불일치] %s", ve)
                    continue
                if not check_missing(t, ["keyword", "score", "timestamp"], symbol=symbol):
                    logger.warning("[소셜미디어] 결측 필드/스키마 불일치: %s", t)
                    continue
                valid_trends.append(trend_obj.dict())
            valid_trends = check_duplicates(valid_trends, ["keyword", "timestamp"], symbol=symbol)

            if not valid_trends:
                write_log(symbol, "social_media", "유효 트렌드 없음/이상치")
                logger.warning("[소셜미디어] 유효 트렌드 없음, fallback 반환")
                save_collector_data(symbol, "social_media_error", {"error": "no_valid_trends", "ts": datetime.utcnow().isoformat()})
                return fallback

            save_collector_data(symbol, "social_media", valid_trends)
            write_log(symbol, "social_media", f"트렌드 수집 성공 | 건수: {len(valid_trends)}")

            duration = int((time.time() - start) * 1000)
            logger.info("[Collector][social_media] 종료, 수집=%d, 실행시간=%dms", len(valid_trends), duration)
            return valid_trends
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            logger.error("[Collector][social_media] 장애 발생: %s, 실행시간=%dms", e, duration)
            write_log(symbol, "social_media", f"트렌드 수집 장애: {str(e)}")
            save_collector_data(symbol, "social_media_error", {"error": str(e), "ts": datetime.utcnow().isoformat()})
            return ctx.get("prev_trends", [])
