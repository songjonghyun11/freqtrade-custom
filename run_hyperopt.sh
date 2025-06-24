docker run --rm \
  -v "$(pwd)/user_data:/freqtrade/user_data" \
  --entrypoint freqtrade \
  -it freqtradeorg/freqtrade:stable \
  hyperopt \
    --config /freqtrade/user_data/config_spot.json \
    --strategy-path /freqtrade/user_data/strategies \
    --strategy HybridAlligatorATRRelaxedStrategy \
    --hyperopt-loss SortinoHyperOptLoss \
    --spaces buy sell roi stoploss \
    --timeframe 5m \
    --timerange 20250401-20250501 \
    -e 200 \
    -j 4 \
    -v

# 실전/최종 검증 전에는 반드시 아래처럼 timerange 전체로 복원!
# --timerange 20250101-20250510