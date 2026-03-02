from dataclasses import dataclass
from typing import List, Optional
from abc import ABC, abstractmethod
import pandas as pd
from pandas import DataFrame
from mysignal import Direction


@dataclass
class Signal:
    def __init__(
        self,
        name: str,
        indexes: List[int],
        direction: Direction,
        weight: Optional[float] = 1.0,
        confidence: Optional[float] = None,
        score: Optional[float] = None,
        meta: Optional[dict] = None,
    ):
        self.name = name
        self.indexes = indexes
        self.direction = direction
        self.weight = weight
        self.confidence = confidence
        self.score = score
        self.meta = meta or {}

    def merge(self, df: DataFrame) -> DataFrame:
        df[f'enter_{self.direction.value}'] = 0
        df.loc[self.indexes, f'enter_{self.direction.value}'] = 1
        df.loc[self.indexes, 'enter_tag'] = self.name  # self.tag 아님!
        return df

    def __repr__(self):
        return (
            f"Signal({self.name}, indexes={self.indexes}, "
            f"direction={self.direction}, weight={self.weight}, "
            f"confidence={self.confidence}, score={self.score})"
        )

class IEntrySignal(ABC):
    @abstractmethod
    def generate(self, dataframe: pd.DataFrame, pair: str, params: dict) -> Signal:
        pass


class IExitSignal(ABC):
    @abstractmethod
    def generate(self, dataframe: pd.DataFrame, pair: str, params: dict) -> pd.Series:
        pass


class IShortSignal(ABC):
    @abstractmethod
    def generate(self, dataframe: pd.DataFrame, pair: str, params: dict) -> pd.Series:
        pass


class IRiskManager(ABC):
    @abstractmethod
    def calculate_stoploss(self, entry_price: float, atr: float) -> float:
        pass


class IRiskManagement(ABC):
    @abstractmethod
    def adjust_stoploss(self, trade, current_rate, params):
        pass
