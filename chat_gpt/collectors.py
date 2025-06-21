# ===== /home/stongone123/freqtrade/src/collectors/interfaces.py 시작 =====
# src/collectors/interfaces.py
from abc import ABC, abstractmethod

class ICollector(ABC):
    @abstractmethod
    def fetch(self, ctx):
        pass

# ===== /home/stongone123/freqtrade/src/collectors/interfaces.py 끝 =====

# ===== /home/stongone123/freqtrade/src/collectors/__init__.py 시작 =====

# ===== /home/stongone123/freqtrade/src/collectors/__init__.py 끝 =====

# ===== /home/stongone123/freqtrade/src/collectors/quality_guard.py 시작 =====
import logging
import os
import json
from datetime import datetime

def write_quality_log(symbol, issue_type, message):
    log_path = f"logs/{symbol}.log"
    with open(log_path, "a", encoding="utf-8") as logf:
        logf.write(f"[{datetime.utcnow().isoformat()}][quality:{issue_type}] {message}\n")

def backup_quality_issue(symbol, issue_type, data):
    backup_dir = "backup"
    os.makedirs(backup_dir, exist_ok=True)
    backup_path = f"{backup_dir}/{symbol}_quality_{issue_type}_{datetime.utcnow().strftime('%Y%m%d')}.bak"
    with open(backup_path, "a", encoding="utf-8") as bakf:
        bakf.write(json.dumps({"ts": datetime.utcnow().isoformat(), "issue": issue_type, "data": data}, ensure_ascii=False) + "\n")

def check_missing(record, required_fields, symbol=None):
    """
    필수 필드가 누락됐는지 검사 + 품질로그/백업 자동 기록 (symbol이 있으면 코인별 파일로)
    """
    for field in required_fields:
        if record.get(field) is None:
            msg = f"[Quality] 결측 필드: {field} / 데이터: {record}"
            logging.warning(msg)
            if symbol:
                write_quality_log(symbol, "missing", f"필드 결측: {field} / 데이터: {record}")
                backup_quality_issue(symbol, "missing", record)
            return False
    return True

def check_duplicates(records, key_fields, symbol=None):
    """
    key_fields 값이 중복된 데이터 필터 + 품질로그/백업 자동 기록 (symbol이 있으면 코인별 파일로)
    """
    seen = set()
    filtered = []
    for rec in records:
        key = tuple(rec.get(f) for f in key_fields)
        if key not in seen:
            seen.add(key)
            filtered.append(rec)
        else:
            msg = f"[Quality] 중복 데이터 스킵: {rec}"
            logging.info(msg)
            if symbol:
                write_quality_log(symbol, "duplicate", f"중복 데이터: {rec}")
                backup_quality_issue(symbol, "duplicate", rec)
    return filtered

# ===== /home/stongone123/freqtrade/src/collectors/quality_guard.py 끝 =====

# ===== /home/stongone123/freqtrade/src/collectors/social_media.py 시작 =====
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

# ===== /home/stongone123/freqtrade/src/collectors/social_media.py 끝 =====

# ===== /home/stongone123/freqtrade/src/collectors/youtube.py 시작 =====
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

# ===== /home/stongone123/freqtrade/src/collectors/youtube.py 끝 =====

# ===== /home/stongone123/freqtrade/src/collectors/models.py 시작 =====
from pydantic import BaseModel
from typing import List, Optional

# 1. 뉴스 데이터 모델
class NewsData(BaseModel):
    title: str
    summary: Optional[str] = None
    url: Optional[str] = None
    timestamp: int

# 2. 오더북 데이터 모델
class OrderbookData(BaseModel):
    symbol: str
    bids: Optional[list] = None  # [(가격, 수량), ...]
    asks: Optional[list] = None
    timestamp: int

# 3. 공포·탐욕지수 데이터 모델
class FearGreedData(BaseModel):
    value: float           # 탐욕/공포 수치 (예: 72.0)
    value_classification: str  # (예: "Greed", "Fear")
    timestamp: int

# 4. 펀딩레이트 데이터 모델
class FundingRateData(BaseModel):
    symbol: str
    funding_rate: float
    timestamp: int

# 5. 소셜미디어 트렌드 데이터 모델
class SocialMediaTrend(BaseModel):
    keyword: str
    score: float
    timestamp: int

# 6. (필요시) 기타 데이터 모델도 여기에 추가
# 예시: YoutubeData, ChartVisionData 등
# ===== /home/stongone123/freqtrade/src/collectors/models.py 끝 =====

# ===== /home/stongone123/freqtrade/src/collectors/funding_rate.py 시작 =====
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

# ===== /home/stongone123/freqtrade/src/collectors/funding_rate.py 끝 =====

# ===== /home/stongone123/freqtrade/src/collectors/chart_vision.py 시작 =====
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

# ===== /home/stongone123/freqtrade/src/collectors/chart_vision.py 끝 =====

# ===== /home/stongone123/freqtrade/src/collectors/news.py 시작 =====
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
# ===== /home/stongone123/freqtrade/src/collectors/news.py 끝 =====

# ===== /home/stongone123/freqtrade/src/collectors/fear_greed.py 시작 =====
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

# ===== /home/stongone123/freqtrade/src/collectors/fear_greed.py 끝 =====

# ===== /home/stongone123/freqtrade/src/collectors/fear_greed_real.py 시작 =====
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

# ===== /home/stongone123/freqtrade/src/collectors/fear_greed_real.py 끝 =====

# ===== /home/stongone123/freqtrade/src/collectors/orderbook.py 시작 =====
import requests, time, logging, os, json
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
from .models import OrderbookData
from pydantic import ValidationError
from .quality_guard import check_missing, check_duplicates
from datetime import datetime

logger = logging.getLogger("collectors.orderbook")

def save_collector_data(symbol, collector_name, data):
    folder = f"data/{symbol}"; os.makedirs(folder, exist_ok=True)
    with open(f"{folder}/{collector_name}.json", "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.utcnow().isoformat(), "data": data}, ensure_ascii=False) + "\n")
    backup_dir = "backup"; os.makedirs(backup_dir, exist_ok=True)
    with open(f"{backup_dir}/{symbol}_{collector_name}_{datetime.utcnow().strftime('%Y%m%d')}.bak", "a", encoding="utf-8") as bakf:
        bakf.write(json.dumps({"ts": datetime.utcnow().isoformat(), "data": data}, ensure_ascii=False) + "\n")

def write_log(symbol, collector_name, message):
    log_path = f"logs/{symbol}.log"
    with open(log_path, "a", encoding="utf-8") as logf:
        logf.write(f"[{datetime.utcnow().isoformat()}][{collector_name}] {message}\n")

class OrderbookCollector(ICollector):
    def fetch(self, ctx):
        start = time.time(); symbol = ctx.get("symbol", "UNKNOWN")
        logger.info("[Collector][orderbook] 시작")
        try:
            def _api_call(timeout):
                response = requests.get("https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=5", timeout=timeout)
                if response.status_code != 200: raise Exception(f"비정상 응답: {response.status_code}")
                return [response.json()]

            fallback = ctx.get("prev_orderbook", [{
                "symbol": symbol,
                "bids": [["100.0", "1.0"]],
                "asks": [["101.0", "1.5"]],
                "timestamp": int(time.time())
            }])

            orderbooks = fetch_with_retry(_api_call, fallback=fallback)
            valid_obs = []
            for ob in orderbooks:
                try:
                    ob_obj = OrderbookData(**ob)
                except ValidationError as ve:
                    logger.warning("[오더북 스키마 결측/불일치] %s", ve)
                    continue
                if not check_missing(ob, ["symbol", "bids", "asks", "timestamp"]):
                    logger.warning("[오더북] 결측 필드/스키마 불일치: %s", ob)
                    continue
                valid_obs.append(ob_obj.dict())
            valid_obs = check_duplicates(valid_obs, ["symbol", "timestamp"])

            save_collector_data(symbol, "orderbook", valid_obs)
            if not valid_obs:
                write_log(symbol, "orderbook", "수집 데이터 없음/이상치")
                logger.warning("[오더북] 유효 오더북 없음, fallback 반환")
                return fallback
            duration = int((time.time() - start) * 1000)
            logger.info("[Collector][orderbook] 종료, 수집=%d, 실행시간=%dms", len(valid_obs), duration)
            write_log(symbol, "orderbook", f"수집 정상 | 건수: {len(valid_obs)}")
            return valid_obs
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            logger.error("[Collector][orderbook] 장애 발생: %s, 실행시간=%dms", e, duration)
            write_log(symbol, "orderbook", f"오더북 수집 장애: {str(e)}")
            save_collector_data(symbol, "orderbook_error", {"error": str(e), "ts": datetime.utcnow().isoformat()})
            return {
                "symbol": symbol,
                "bids": [["100.0", "1.0"]],
                "asks": [["101.0", "1.5"]],
                "timestamp": int(time.time())
            }

def fetch_orderbook(symbol: str):
    return OrderbookCollector().fetch({"symbol": symbol})

# ===== /home/stongone123/freqtrade/src/collectors/orderbook.py 끝 =====

# ===== /home/stongone123/freqtrade/src/collectors/orderbook_real.py 시작 =====
import requests, time, logging, os, json
from .interfaces import ICollector
from ..utils.common import fetch_with_retry
from .models import OrderbookData
from pydantic import ValidationError
from .quality_guard import check_missing, check_duplicates
from datetime import datetime

logger = logging.getLogger("collectors.orderbook")

def save_collector_data(symbol, collector_name, data):
    folder = f"data/{symbol}"; os.makedirs(folder, exist_ok=True)
    with open(f"{folder}/{collector_name}.json", "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.utcnow().isoformat(), "data": data}, ensure_ascii=False) + "\n")
    backup_dir = "backup"; os.makedirs(backup_dir, exist_ok=True)
    with open(f"{backup_dir}/{symbol}_{collector_name}_{datetime.utcnow().strftime('%Y%m%d')}.bak", "a", encoding="utf-8") as bakf:
        bakf.write(json.dumps({"ts": datetime.utcnow().isoformat(), "data": data}, ensure_ascii=False) + "\n")

def write_log(symbol, collector_name, message):
    log_path = f"logs/{symbol}.log"
    with open(log_path, "a", encoding="utf-8") as logf:
        logf.write(f"[{datetime.utcnow().isoformat()}][{collector_name}] {message}\n")

class OrderbookCollector(ICollector):
    def fetch(self, ctx):
        start = time.time(); symbol = ctx.get("symbol", "UNKNOWN")
        logger.info("[Collector][orderbook] 시작")
        try:
            def _api_call(timeout):
                response = requests.get(f"https://api.binance.com/api/v3/depth?symbol={symbol}USDT&limit=5", timeout=timeout)
                if response.status_code != 200: raise Exception(f"비정상 응답: {response.status_code}")
                data = response.json()
                return [{
                    "symbol": symbol,
                    "bids": data.get("bids", []),
                    "asks": data.get("asks", []),
                    "timestamp": int(time.time())
                }]

            fallback = ctx.get("prev_orderbook", [{
                "symbol": symbol,
                "bids": [["100.0", "1.0"]],
                "asks": [["101.0", "1.5"]],
                "timestamp": int(time.time())
            }])

            orderbooks = fetch_with_retry(_api_call, fallback=fallback)
            valid_obs = []
            for ob in orderbooks:
                try:
                    ob_obj = OrderbookData(**ob)
                except ValidationError as ve:
                    logger.warning("[오더북 스키마 결측/불일치] %s", ve)
                    continue
                if not check_missing(ob, ["symbol", "bids", "asks", "timestamp"]):
                    logger.warning("[오더북] 결측 필드/스키마 불일치: %s", ob)
                    continue
                valid_obs.append(ob_obj.model_dump())
            valid_obs = check_duplicates(valid_obs, ["symbol", "timestamp"])

            save_collector_data(symbol, "orderbook", valid_obs)
            if not valid_obs:
                write_log(symbol, "orderbook", "수집 데이터 없음/이상치")
                logger.warning("[오더북] 유효 오더북 없음, fallback 반환")
                return fallback[0]
            duration = int((time.time() - start) * 1000)
            logger.info("[Collector][orderbook] 종료, 수집=%d, 실행시간=%dms", len(valid_obs), duration)
            write_log(symbol, "orderbook", f"수집 정상 | 건수: {len(valid_obs)}")
            return valid_obs[0]
        except Exception as e:
            duration = int((time.time() - start) * 1000)
            logger.error("[Collector][orderbook] 장애 발생: %s, 실행시간=%dms", e, duration)
            write_log(symbol, "orderbook", f"오더북 수집 장애: {str(e)}")
            save_collector_data(symbol, "orderbook_error", {"error": str(e), "ts": datetime.utcnow().isoformat()})
            return {
                "symbol": symbol,
                "bids": [["100.0", "1.0"]],
                "asks": [["101.0", "1.5"]],
                "timestamp": int(time.time())
            }

def fetch_orderbook(symbol: str):
    return OrderbookCollector().fetch({"symbol": symbol})

# ===== /home/stongone123/freqtrade/src/collectors/orderbook_real.py 끝 =====

