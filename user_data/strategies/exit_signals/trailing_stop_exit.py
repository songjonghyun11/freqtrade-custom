from interfaces import IExitSignal
import pandas as pd

class TrailingStopExitSignal(IExitSignal):
    def generate(self, df: pd.DataFrame, pair: str, params: dict):
        trail_perc = params.get("trail_perc", 0.02)
        # entry_price, current_price 컬럼이 모두 있어야 작동
        if ("entry_price" not in df.columns) or ("current_price" not in df.columns):
            return pd.Series([False] * len(df), index=df.index)
        # 최고가를 DataFrame에서 계산
        highest = df["current_price"].cummax()
        exit_cond = df["current_price"] <= highest * (1 - trail_perc)
        return exit_cond.fillna(False)
