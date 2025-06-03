import pytest
from src.utils.config import load_config

def test_valid_config():
    # 정상 config 파일은 에러 없이 로드
    settings = load_config("config/config_dev.json")
    assert settings.entry_signals
    assert settings.env == "dev"

def test_missing_required_field(tmp_path):
    # 필수 필드 누락 시 에러 발생
    d = tmp_path / "bad.json"
    d.write_text('{"short_signals":[]}')
    with pytest.raises(Exception):
        load_config(str(d))

def test_wrong_type(tmp_path):
    # 타입 오류(숫자 대신 문자열) 시 에러 발생
    d = tmp_path / "bad2.json"
    d.write_text('{"entry_signals": [], "short_signals": [], "signal_threshold": "not_a_number", "signal_weights": {}, "min_signal_count": 1, "env": "dev"}')
    with pytest.raises(Exception):
        load_config(str(d))
