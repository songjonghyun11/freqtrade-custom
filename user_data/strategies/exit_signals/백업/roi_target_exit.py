from interfaces import IExitSignal
import pandas as pd

class ROITargetExitSignal(IExitSignal):
    def generate(self, df: pd.DataFrame, pair: str, params: dict):
        roi_target = params.get("roi_target", 0.04)  # 4% 디폴트
        # entry_price, current_price 컬럼이 모두 있어야 작동
        if ("entry_price" not in df.columns) or ("current_price" not in df.columns):
            return pd.Series([False] * len(df), index=df.index)
        roi = (df["current_price"] - df["entry_price"]) / df["entry_price"]
        exit_cond = roi >= roi_target
        return exit_cond.fillna(False)
