import pandas as pd
from modules.exit_signal import ExitSignal

def make_df():
    return pd.DataFrame({
        'lips':  [5,4,3,2,1],
        'teeth': [1,2,3,4,5]
    })

def test_generate_long_exit_signal():
    es = ExitSignal({})
    df = make_df()
    sig = es.generate_long(df)
    assert isinstance(sig.iloc[-1], (bool,))  # 마지막이 bool
    assert sig.sum() == 1                     # 한 번만 True
