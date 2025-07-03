import requests
import time
import logging
import os
import json
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
from .quality_guard import check_missing
from datetime import datetime

logger = logging.getLogger("collectors.youtube")

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

class YoutubeCollector(ICollector):
    def fetch(self, ctx):
        start = time.time()
        symbol = ctx.get("symbol", "UNKNOWN")
        logger.info("[Collector][youtube] 시작")
        try:
            def _api_call(timeout):
                video_id = ctx.get("video_id", "예시값")
                response = requests.get(
                    f"https://www.googleapis.com/youtube/v3/captions?videoId={video_id}",
                    timeout=timeout
                )
                if response.status_code != 200:
                    raise Exception(f"비정상 응답: {response.status_code}")
                data = response.json()
                if not data:
                    raise Exception("유튜브 캡션 데이터 없음")
                return data

            fallback = ctx.get("prev_caption", {})
            result = fetch_with_retry(_api_call, fallback=fallback)

            if not check_missing(result, ["caption", "timestamp"], symbol=symbol):
                write_log(symbol, "youtube", "결측 필드/스키마 불일치, fallback 사용")
                save_collector_data(symbol, "youtube_error", {"error": "missing field", "data": result, "ts": datetime.utcnow().isoformat()})
                logger.warning("[유튜브] 결측 필드/스키마 불일치, fallback 사용: %s", result)
                return fallback

            save_collector_data(symbol, "youtube", result)
            write_log(symbol, "youtube", "유튜브 캡션 수집 성공")
            duration = int((time.time() - start) * 1000)
            logger.info("[Collector][youtube] 종료, 수집 1건, 실행시간=%dms", duration)
            return result
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            logger.error("[Collector][youtube] 장애 발생: %s, 실행시간=%dms", e, duration)
            write_log(symbol, "youtube", f"유튜브 캡션 수집 장애: {str(e)}")
            save_collector_data(symbol, "youtube_error", {"error": str(e), "ts": datetime.utcnow().isoformat()})
            return ctx.get("prev_caption", {})
