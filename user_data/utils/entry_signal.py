# modules/entry_signal.py
import pandas as pd

class EntrySignal:
    def __init__(self, params: dict):
        self.atr_period      = params["atr_period"]
        self.vol_multiplier  = params["vol_multiplier"]
        self.volat_threshold = params["volat_threshold"]
        self.high_lookback   = params["high_lookback"]

    def generate_long(self, df: pd.DataFrame) -> pd.Series:
        # breakout, volume, volatility 필터
        breakout      = df['close'] > (df['close'].shift(1) + df['atr'])
        volume_ok     = df['volume'] > df['vol_ma'] * self.vol_multiplier
        volatility_ok = df['atr'] > (df['close'] * self.volat_threshold)
        return breakout & volume_ok & volatility_ok

    def generate_short(self, df: pd.DataFrame) -> pd.Series:
        breakout_short = df['close'] < (df['close'].shift(1) - df['atr'])
        volume_ok      = df['volume'] > df['vol_ma'] * self.vol_multiplier
        volatility_ok  = df['atr'] > (df['close'] * self.volat_threshold)
        return breakout_short & volume_ok & volatility_ok
