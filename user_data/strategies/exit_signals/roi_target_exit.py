import pandas as pd
from interfaces import IExitSignal, Signal
from mysignal import Direction

class ROITargetExitSignal(IExitSignal):
    def generate(self, ctx_or_df, symbol: str, params: dict, position=None) -> Signal:
        if isinstance(ctx_or_df, pd.DataFrame):
            df = ctx_or_df
        else:
            df = ctx_or_df[symbol]["ohlcv"]

        roi_target = params.get("roi_target", 0.04)  # 4% 디폴트

        # entry_price, current_price 컬럼이 모두 있어야 작동
        if ("entry_price" not in df.columns) or ("current_price" not in df.columns):
            indexes = []
        else:
            roi = (df["current_price"] - df["entry_price"]) / df["entry_price"]
            exit_cond = roi >= roi_target
            indexes = list(df.index[exit_cond.fillna(False)])

        return Signal(
            name="roi_target_exit",
            indexes=indexes,
            direction=Direction.EXIT,
            score=1.0,
            meta={
                "roi_target": roi_target,
            }
        )
