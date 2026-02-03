import pandas as pd
import talib.abstract as ta  # 아직 다른 데서 쓸 수 있으니 놔둠
from interfaces import IExitSignal, Signal
from mysignal import Direction


class EMACrossExit(IExitSignal):
    def generate(self, ctx_or_df, symbol: str, params: dict, position=None) -> Signal:
        """
        단순 EMA 하향 교차 기반 EXIT 시그널

        - fast_ema가 slow_ema를 위에서 아래로 뚫고 내려올 때 EXIT
        - hyperopt / overrides에서 넘어오는 파라미터는 .value를 인식해서 정수로 캐스팅
        """
        # 1) dataframe 확보
        if isinstance(ctx_or_df, pd.DataFrame):
            df = ctx_or_df
        else:
            df = ctx_or_df[symbol]["ohlcv"]

        if df is None or df.empty:
            return Signal(
                name="ema_cross_exit",
                indexes=[],
                direction=Direction.EXIT,
                score=0.0,
                meta={"reason": "empty_df"},
            )

        # 2) 파라미터 처리 (hyperopt .value 포함) + 안전장치
        fast = params.get("exit_fast_ema", 9)
        slow = params.get("exit_slow_ema", 21)

        # hyperopt 객체면 .value, 아니면 그대로
        fast = fast.value if hasattr(fast, "value") else fast
        slow = slow.value if hasattr(slow, "value") else slow

        # 정수 캐스팅 + 최소값 보정
        fast = int(fast) if fast is not None else 9
        slow = int(slow) if slow is not None else 21

        if fast < 1:
            fast = 1
        if slow < 2:
            slow = 2
        # slow가 fast보다 항상 길도록 강제
        if slow <= fast:
            slow = fast + 1

        # 3) EMA 계산 (pandas ewm 사용해서 인덱스 보존)
        close = df["close"].astype(float)

        fast_ema = close.ewm(span=fast, adjust=False).mean()
        slow_ema = close.ewm(span=slow, adjust=False).mean()

        # 4) 하향 교차 조건
        #    이전 캔들: fast >= slow
        #    현재 캔들: fast < slow
        cond_now = fast_ema < slow_ema
        cond_prev = fast_ema.shift(1) >= slow_ema.shift(1)

        exit_cross = (cond_now & cond_prev).fillna(False)

        # 5) 인덱스는 df.index 그대로 사용 (DatetimeIndex 유지)
        indexes = list(df.index[exit_cross])

        return Signal(
            name="ema_cross_exit",
            indexes=indexes,
            direction=Direction.EXIT,
            score=1.0,
            meta={
                "exit_fast_ema": fast,
                "exit_slow_ema": slow,
                "n_signals": len(indexes),
            },
        )
