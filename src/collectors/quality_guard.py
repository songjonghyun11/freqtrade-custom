# src/collectors/quality_guard.py

import logging

def check_missing(record, required_fields):
    for field in required_fields:
        if record.get(field) is None:
            logging.warning(f"[Quality] 결측 필드: {field} / 데이터: {record}")
            return False
    return True

def check_duplicates(records, key_fields):
    seen = set()
    filtered = []
    for rec in records:
        key = tuple(rec.get(f) for f in key_fields)
        if key not in seen:
            seen.add(key)
            filtered.append(rec)
        else:
            logging.info(f"[Quality] 중복 데이터 스킵: {rec}")
    return filtered

# (선택) 스키마/타입 검사 등 더 추가하고 싶으면 이 파일에 함수로 추가 가능!
