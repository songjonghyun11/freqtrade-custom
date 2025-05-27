# bootstrap.py

import importlib
from src.utils.config import ConfigLoader
from src.utils.logger import setup_logger
from src.persistence.database_manager import DatabaseManager
from src.strategies.strategy_orchestrator import StrategyOrchestrator

def bootstrap(
    config_path: str = "config/entry_signals.json",
    db_url: str = "sqlite:///trade_reflection.db"
) -> StrategyOrchestrator:
    # 1) 설정 파일 로드
    cfg = ConfigLoader().load(config_path)

    # 2) 로거 초기화
    setup_logger("freqtrade")

    # 3) DB 연결
    dbm = DatabaseManager(db_url=db_url)

    # 4) Orchestrator 초기화
    orchestrator = StrategyOrchestrator(
        entry_signals=cfg.get("entry_signals", []),
        short_signals=cfg.get("short_signals", []),
        exit_signals=cfg.get("exit_signals", []),
        risk_managers=cfg.get("risk_managers", []),
    )
    return orchestrator

if __name__ == "__main__":
    agg = bootstrap()
    print("Bootstrap completed:", agg)
