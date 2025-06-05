import json
import jsonschema
from pydantic import BaseModel, ValidationError
from typing import Optional, List, Dict
from src.utils.config_history import add_settings_history

class RiskManagement(BaseModel):
    max_drawdown: Optional[float]
    value_at_risk: Optional[float]

class Settings(BaseModel):
    entry_signals: List[str]
    short_signals: List[str]
    exit_signals: Optional[List[str]]
    signal_threshold: float
    signal_weights: Dict[str, float]
    api_keys: Optional[Dict[str, str]]
    min_signal_count: int
    env: str
    feature_flags: Optional[Dict[str, bool]]
    risk_management: Optional[RiskManagement]
    backtest: Optional[Dict]
    alerts: Optional[Dict]
    dashboard: Optional[Dict]
    slippage: Optional[float]
    fee: Optional[float]

def load_config(config_path="config/config_dev.json", schema_path="schemas/config_schema.json"):
    with open(config_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if schema_path:
        with open(schema_path, "r", encoding="utf-8") as sf:
            schema = json.load(sf)
        jsonschema.validate(instance=raw, schema=schema)
    try:
        settings = Settings(**raw)
        add_settings_history(config_path)
        return settings
    except ValidationError as e:
        print("⚠️ ValidationError!\n", e)
        raise