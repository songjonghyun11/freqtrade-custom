# modules/exit_signal.py

import pandas as pd
from pandas import DataFrame, Series

class ExitSignal:
    def __init__(self, params: dict):
        # 필요시 파라미터 초기화
        pass

    def generate_long(self, df: DataFrame) -> Series:
        """
        Alligator lips가 teeth 아래로 교차할 때만
        롱 청산 시그널(True) 반환 (Python bool)
        """
        cond = df['lips'] < df['teeth']
        prev = df['lips'].shift(1) >= df['teeth'].shift(1)
        signal = (cond & prev).fillna(False)

        # Python bool 리스트로 변환
        py_list = [bool(val) for val in signal.tolist()]
        # object dtype Series로 만들어 Python bool 유지
        return pd.Series(py_list, index=signal.index, dtype=object)

    def generate_short(self, df: DataFrame) -> Series:
        """
        Alligator lips가 teeth 위로 교차할 때만
        숏 청산 시그널(True) 반환 (Python bool)
        """
        cond = df['lips'] > df['teeth']
        prev = df['lips'].shift(1) <= df['teeth'].shift(1)
        signal = (cond & prev).fillna(False)

        py_list = [bool(val) for val in signal.tolist()]
        return pd.Series(py_list, index=signal.index, dtype=object)
