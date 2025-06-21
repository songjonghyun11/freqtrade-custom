import requests
import logging
import os
import json
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
from .models import FundingRateData
from pydantic import ValidationError
from .quality_guard import check_missing
from datetime import datetime

logger = logging.getLogger("collectors.funding_rate")

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

class FundingRateCollector(ICollector):
    def fetch(self, ctx):
        logger.info("[Collector][funding_rate] 시작")
        symbol = ctx.get("symbol", "UNKNOWN")
        try:
            def _api_call(timeout):
                response = requests.get("https://api.fundingrate.example.com/latest", timeout=timeout)
                if response.status_code != 200:
                    raise Exception(f"비정상 응답: {response.status_code}")
                data = response.json()
                if not data:
                    raise Exception("펀딩비 데이터 없음")
                return data

            fallback = ctx.get("prev_funding_rate", {})
            result = fetch_with_retry(_api_call, fallback=fallback)

            try:
                fr_obj = FundingRateData(**result)
            except ValidationError as ve:
                logger.warning("[펀딩비 스키마 결측/불일치] %s", ve)
                write_log(symbol, "funding_rate", f"스키마 결측/불일치: {str(ve)}")
                save_collector_data(symbol, "funding_rate_error", {"error": str(ve), "ts": datetime.utcnow().isoformat()})
                return fallback

            if not check_missing(fr_obj.dict(), ["symbol", "rate", "timestamp"], symbol=symbol):
                logger.warning("[펀딩비] 결측 필드/스키마 불일치, fallback 사용: %s", result)
                write_log(symbol, "funding_rate", f"결측 필드/스키마 불일치, fallback 사용")
                save_collector_data(symbol, "funding_rate_error", {"error": "missing field", "data": result, "ts": datetime.utcnow().isoformat()})
                return fallback

            save_collector_data(symbol, "funding_rate", fr_obj.dict())
            write_log(symbol, "funding_rate", "펀딩레이트 수집 성공")

            logger.info("[Collector][funding_rate] 종료, 수집 1건")
            return fr_obj.dict()
        except Exception as e:
            logger.error("[Collector][funding_rate] 장애 발생: %s", e)
            write_log(symbol, "funding_rate", f"펀딩레이트 수집 장애: {str(e)}")
            save_collector_data(symbol, "funding_rate_error", {"error": str(e), "ts": datetime.utcnow().isoformat()})
            return ctx.get("prev_funding_rate", {})
