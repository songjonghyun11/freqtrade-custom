import numpy as np

def calculate_var(equity_curve, confidence_level=0.95, window=30):
    # 최근 window(예: 30일) 수익률의 VAR 계산
    returns = np.diff(equity_curve) / equity_curve[:-1]
    if len(returns) < window:
        return None
    sorted_losses = np.sort(returns[-window:])
    var_idx = int((1-confidence_level)*window)
    return sorted_losses[var_idx]

def calculate_mdd(equity_curve):
    # 누적수익곡선에서 최대낙폭(MDD) 계산
    peak = equity_curve[0]
    mdd = 0
    for x in equity_curve:
        if x > peak:
            peak = x
        dd = (x-peak)/peak
        mdd = min(mdd, dd)
    return mdd
