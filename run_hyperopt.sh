#!/usr/bin/env bash
# run_hyperopt.sh

docker run --rm \
  -v "$HOME/freqtrade/user_data:/freqtrade/user_data" \
  --entrypoint freqtrade \
  -it freqtradeorg/freqtrade:stable \
  hyperopt \
    --config /freqtrade/user_data/config_spot.json \
    --strategy-path /freqtrade/user_data/strategies \
    --strategy HybridAlligatorATRRelaxedStrategy \
    --hyperopt-loss SortinoHyperOptLoss \
    --spaces buy sell \
    --timeframe 5m \
    --timerange 20250101-20250401 \
    -e 200 \
    -j 1 \
    -v
