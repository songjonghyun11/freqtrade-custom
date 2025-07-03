import logging
from datetime import datetime
from pydantic import ValidationError

from .interfaces import ICollector
from .models import FearGreedData
from .quality_guard import check_missing
from ..utils.common import fetch_with_retry

logger = logging.getLogger(__name__)

def fetch_fear_greed(symbol: str) -> dict:
    logger.info("[Collector][fear_greed] 시작")

    url = "https://api.alternative.me/fng/?limit=1&format=json"
    try:
        res = fetch_with_retry(url, method="GET", retries=3)
        data = res.get("data", [{}])[0]
    except Exception as e:
        logger.error(f"[공포탐욕][{symbol}] fetch 실패 - fallback 반환: {e}")
        return {
            "value": 50,
            "value_classification": "Neutral",
            "timestamp": int(datetime.now().timestamp())
        }

    try:
        fg_obj = FearGreedData(
            value=int(data.get("value")),
            value_classification=data.get("value_classification", "Unknown"),
            timestamp=int(data.get("timestamp", datetime.now().timestamp()))
        )
    except ValidationError as ve:
        logger.warning(f"[공포탐욕 스키마 결측/불일치] {ve}")
        return {
            "value": 50,
            "value_classification": "Neutral",
            "timestamp": int(datetime.now().timestamp())
        }

    if not check_missing(fg_obj.model_dump(), ["value", "value_classification", "timestamp"], symbol=symbol):
        return {
            "value": 50,
            "value_classification": "Neutral",
            "timestamp": int(datetime.now().timestamp())
        }

    return fg_obj.model_dump()
