#!/usr/bin/env bash

# Spot 모드 백테스트 → config_spot.json 사용
docker run --rm \
  -v "$HOME/freqtrade/user_data:/freqtrade/user_data" \
  --entrypoint freqtrade \
  -it freqtradeorg/freqtrade:stable \
  backtesting \
    --config /freqtrade/user_data/config_spot.json \
    --strategy HybridAlligatorATRRelaxedStrategy \
    --timerange 20250101-20250510 \
    --timeframe 5m \
    --export trades \
    --export-filename /freqtrade/user_data/trades_spot.json \
    -v
