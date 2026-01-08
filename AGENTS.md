# Project: freqtrade (WSL+Docker)

## Environment
- Root: ~/freqtrade
- Docker image: freqtradeorg/freqtrade:stable
- No Windows/WSL path mixing.

## Hard rules
- Do NOT use unsupported freqtrade options.
- Any config edits must keep backups and provide rollback.
- Always show `git diff` after modifications.

## Key files
- Strategy: user_data/strategies/TestDonchianFearGreedStrategy.py
- Config: user_data/config/config_spot.json
- Overrides: user_data/overrides/*
- Sweep logs: user_data/backtest_results/_sweep_logs/*

## Default verification commands (prefer docker)
- Backtest (example):
  docker run --rm -v "$(pwd)/user_data:/freqtrade/user_data" freqtradeorg/freqtrade:stable \
    backtesting --config /freqtrade/user_data/config/config_spot.json \
    --strategy TestDonchianFearGreedStrategy --strategy-path /freqtrade/user_data/strategies
