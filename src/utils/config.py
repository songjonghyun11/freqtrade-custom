# src/utils/config.py

import json
import jsonschema

class ConfigLoader:
    def load(self, path: str) -> dict:
        """설정 파일 로드 후 JSON 스키마 검증 (간단히 JSON 파싱만)"""
        with open(path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        # TODO: jsonschema.validate(cfg, schema) 등 검증 로직 추가
        return cfg
