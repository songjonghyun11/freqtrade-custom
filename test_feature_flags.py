from src.utils.config import load_config

settings = load_config("config/config_dev.json")

for strategy in settings.entry_signals:
    if settings.feature_flags.get(strategy, True):
        print(f"{strategy} 전략 실행!")
    else:
        print(f"{strategy} 전략 OFF (설정에서 비활성화됨)")

