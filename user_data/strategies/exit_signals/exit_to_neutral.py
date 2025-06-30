# user_data/strategies/exit_signals/exit_to_neutral.py
from interfaces import IExitSignal
import pandas as pd

class ExitToNeutralSignal(IExitSignal):
    def generate(self, df: pd.DataFrame, pair: str, params: dict):
        # 파라미터: neutral_threshold 값이 없으면 0.3 (디폴트)
        threshold = params.get("neutral_threshold", 0.3)
        # DataFrame에 aggregator_score(집계 점수) 컬럼이 있다고 가정
        if "aggregator_score" not in df.columns:
            # 만약 컬럼이 없으면 무조건 False 반환 (에러방지)
            return pd.Series([False] * len(df), index=df.index)
        exit_cond = df["aggregator_score"] < threshold
        return exit_cond.fillna(False)
