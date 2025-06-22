import pandas as pd
import numpy as np
from modules.entry_signal import EntrySignal

def make_df():
    data = {
        'high':  np.linspace(1.1,10.1,10),
        'low':   np.linspace(0.9,9.9,10),
        'close': np.linspace(1,10,10),
        'volume': [100,200,150,300,120,80,250,400,50,100]
    }
    df = pd.DataFrame(data)
    df['atr']    = df['high'].rolling(3).max() - df['low'].rolling(3).min()
    df['vol_ma'] = df['volume'].rolling(3).mean()
    return df

def test_generate_long_returns_boolean_series():
    params = {"atr_period":3, "vol_multiplier":1.0, "volat_threshold":0.0, "high_lookback":1}
    es = EntrySignal(params)
    df = make_df()
    sig = es.generate_long(df)
    assert sig.dtype == bool
    # 시그널 개수가 0 이상 (실행 오류 없이)
    assert sig.sum() >= 0
