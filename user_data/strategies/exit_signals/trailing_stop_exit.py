import pandas as pd
from interfaces import IExitSignal, Signal
from mysignal import Direction

class TrailingStopExitSignal(IExitSignal):
    def generate(self, ctx_or_df, symbol: str, params: dict, position=None) -> Signal:
        if isinstance(ctx_or_df, pd.DataFrame):
            df = ctx_or_df
        else:
            df = ctx_or_df[symbol]["ohlcv"]

        trail_perc = params.get("trail_perc", 0.02)

        # entry_price, current_price 컬럼이 모두 있어야 작동
        if ("entry_price" not in df.columns) or ("current_price" not in df.columns):
            indexes = []
        else:
            highest = df["current_price"].cummax()
            exit_cond = df["current_price"] <= highest * (1 - trail_perc)
            indexes = list(df.index[exit_cond.fillna(False)])

        return Signal(
            name="trailing_stop_exit",
            indexes=indexes,
            direction=Direction.EXIT,
            score=1.0,
            meta={
                "trail_perc": trail_perc,
            }
        )
