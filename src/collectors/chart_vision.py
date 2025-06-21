import requests
import time
import logging
import os
import json
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
from .quality_guard import check_missing
from datetime import datetime

logger = logging.getLogger("collectors.chart_vision")

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

class ChartVisionCollector(ICollector):
    def fetch(self, ctx):
        start = time.time()
        symbol = ctx.get("symbol", "UNKNOWN")
        logger.info("[Collector][chart_vision] 시작")
        try:
            def _api_call(timeout):
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

            fallback = ctx.get("prev_vision", {})
            result = fetch_with_retry(_api_call, fallback=fallback)

            if not check_missing(result, ["chart", "timestamp"], symbol=symbol):
                write_log(symbol, "chart_vision", "결측 필드/스키마 불일치, fallback 사용")
                save_collector_data(symbol, "chart_vision_error", {"error": "missing field", "data": result, "ts": datetime.utcnow().isoformat()})
                logger.warning("[차트비전] 결측 필드/스키마 불일치, fallback 사용: %s", result)
                return fallback

            save_collector_data(symbol, "chart_vision", result)
            write_log(symbol, "chart_vision", "차트비전 수집 성공")
            duration = int((time.time() - start) * 1000)
            logger.info("[Collector][chart_vision] 종료, 수집 1건, 실행시간=%dms", duration)
            return result
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            logger.error("[Collector][chart_vision] 장애 발생: %s, 실행시간=%dms", e, duration)
            write_log(symbol, "chart_vision", f"차트비전 수집 장애: {str(e)}")
            save_collector_data(symbol, "chart_vision_error", {"error": str(e), "ts": datetime.utcnow().isoformat()})
            return ctx.get("prev_vision", {})
