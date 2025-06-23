for symbol in symbols:
    risk_result = DynamicStoploss().apply(ctx, symbol, params, position)
    # 혹은
    mdd_result = PortfolioMDDManager().apply(ctx, symbol, params, position)
    # 결과 확인 후 손절/강제청산 등 실행
