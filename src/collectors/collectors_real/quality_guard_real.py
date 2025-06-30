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
