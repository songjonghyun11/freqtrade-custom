#!/usr/bin/env bash
# run_futures.sh

# 300초(5분) 후 자동 종료
timeout 300 docker run --rm \
  -v "$HOME/freqtrade/user_data:/freqtrade/user_data" \
  --entrypoint freqtrade \
  freqtradeorg/freqtrade:stable \
  trade \
    --config /freqtrade/user_data/config_futures.json \
    --dry-run \
    -v
