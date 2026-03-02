from __future__ import annotations

from typing import Any, Dict
import numpy as np
import pandas as pd
import talib.abstract as ta

from TestDonchianFearGreedStrategy import TestDonchianFearGreedStrategy


class TDFG_GuardV2(TestDonchianFearGreedStrategy):
    """
    Entry guard only (no lookahead).
    - close_pos guard
    - breakout close-confirm (close above dc prev high)
    - volume confirm (vol_ratio OR vol_z)
    - rsi14 min
    """

    # defaults (can override via config strategy_parameters -> TestDonchianFearGreedStrategyFG)
    guard_enable = True

    guard_use_closepos = True
    guard_close_pos_min = 0.35

    guard_use_close_confirm = True  # close must be above dc_high_prev

    guard_use_vol = False
    guard_vol_lookback = 48
    guard_vol_ratio_min = 3.0
    guard_vol_z_min = 1.0

    guard_use_rsi = False
    guard_rsi14_min = 68.0

    guard_dc_period = 20

    def _sp(self) -> Dict[str, Any]:
        sp = (self.config or {}).get("strategy_parameters") or {}
        return sp.get("TestDonchianFearGreedStrategyFG") or {}

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df = super().populate_indicators(dataframe, metadata)

        # RSI14
        if "rsi14" not in df.columns:
            df["rsi14"] = ta.RSI(df, timeperiod=14)

        # Donchian prev high
        per = int(self._sp().get("guard_dc_period", self.guard_dc_period))
        dc_high = df["high"].rolling(per).max()
        df["dc_high_prev"] = dc_high.shift(1)

        # close_pos in candle
        rng = (df["high"] - df["low"]).replace(0, np.nan)
        df["close_pos"] = ((df["close"] - df["low"]) / rng).fillna(0.5).clip(0, 1)

        # volume features
        lb = int(self._sp().get("guard_vol_lookback", self.guard_vol_lookback))
        v = df["volume"].astype(float)
        v_mean = v.rolling(lb).mean()
        v_std = v.rolling(lb).std(ddof=0)
        df["vol_ratio"] = (v / v_mean).replace([np.inf, -np.inf], np.nan)
        df["vol_z"] = ((v - v_mean) / v_std).replace([np.inf, -np.inf], np.nan)

        return df

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df = super().populate_entry_trend(dataframe, metadata)

        sp = self._sp()
        enable = int(sp.get("guard_enable", 1 if self.guard_enable else 0)) == 1
        if not enable:
            return df

        use_closepos = int(sp.get("guard_use_closepos", 1 if self.guard_use_closepos else 0)) == 1
        close_pos_min = float(sp.get("guard_close_pos_min", self.guard_close_pos_min))

        use_close_confirm = int(sp.get("guard_use_close_confirm", 1 if self.guard_use_close_confirm else 0)) == 1

        use_vol = int(sp.get("guard_use_vol", 1 if self.guard_use_vol else 0)) == 1
        vol_ratio_min = float(sp.get("guard_vol_ratio_min", self.guard_vol_ratio_min))
        vol_z_min = float(sp.get("guard_vol_z_min", self.guard_vol_z_min))

        use_rsi = int(sp.get("guard_use_rsi", 1 if self.guard_use_rsi else 0)) == 1
        rsi_min = float(sp.get("guard_rsi14_min", self.guard_rsi14_min))

        g = pd.Series(True, index=df.index)

        if use_closepos:
            g &= (df["close_pos"] >= close_pos_min)

        if use_close_confirm:
            g &= (df["close"] > df["dc_high_prev"])

        if use_vol:
            g &= ((df["vol_ratio"] >= vol_ratio_min) | (df["vol_z"] >= vol_z_min))

        if use_rsi:
            g &= (df["rsi14"] >= rsi_min)

        enter_col = "enter_long" if "enter_long" in df.columns else "buy"
        df.loc[(df[enter_col] == 1) & (~g), enter_col] = 0

        if "enter_tag" in df.columns:
            df.loc[(df[enter_col] == 1) & (g), "enter_tag"] = df["enter_tag"].astype(str) + "&guardv2"

        return df
