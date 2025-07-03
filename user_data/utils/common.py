import time
import logging

logger = logging.getLogger(__name__)

def fetch_with_retry(request_fn, max_retries=3, backoff_base=1, timeout=5, fallback=None):
    for attempt in range(1, max_retries + 1):
        try:
            return request_fn(timeout=timeout)
        except Exception as e:
            logger.warning(f"[재시도] {attempt}회 실패: {e}")
            if attempt < max_retries:
                sleep_sec = backoff_base * (2 ** (attempt - 1))
                time.sleep(sleep_sec)
            else:
                logger.error(f"[최종실패] {max_retries}회 실패: {e}")
                if fallback is not None:
                    logger.warning("[대체값 반환] Fallback 값 사용")
                    return fallback
                else:
                    raise
