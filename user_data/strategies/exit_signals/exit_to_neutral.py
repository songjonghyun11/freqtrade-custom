import pandas as pd
from interfaces import IExitSignal, Signal
from mysignal import Direction

class ExitToNeutralSignal(IExitSignal):
    def generate(self, ctx_or_df, symbol: str, params: dict, position=None) -> Signal:
        if isinstance(ctx_or_df, pd.DataFrame):
            df = ctx_or_df
        else:
            df = ctx_or_df[symbol]["ohlcv"]

        # 하이퍼옵트 파라미터: 집계 점수 threshold
        threshold = params.get("neutral_threshold", 0.3)

        # aggregator_score(집계 점수) 컬럼이 있는지 확인
        if "aggregator_score" not in df.columns:
            indexes = []
        else:
            exit_cond = df["aggregator_score"] < threshold
            indexes = list(df.index[exit_cond.fillna(False)])

        return Signal(
            name="exit_to_neutral",
            indexes=indexes,
            direction=Direction.EXIT,
            score=1.0,
            meta={
                "neutral_threshold": threshold,
            }
        )
