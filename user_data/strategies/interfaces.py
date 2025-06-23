
from abc import ABC, abstractmethod
import pandas as pd

class IEntrySignal(ABC):
    @abstractmethod
    def generate(self, dataframe: pd.DataFrame, pair: str, params: dict) -> pd.Series:
        pass

class IExitSignal(ABC):
    @abstractmethod
    def generate(self, dataframe: pd.DataFrame, pair: str, params: dict) -> pd.Series:
        pass

class IRiskManager(ABC):
    @abstractmethod
    def calculate_stoploss(self, entry_price: float, atr: float) -> float:
        pass

class IShortSignal(ABC):
    @abstractmethod
    def generate(self, dataframe: pd.DataFrame, pair: str, params: dict) -> pd.Series:
        pass

class IRiskManagement(ABC):
    @abstractmethod
    def adjust_stoploss(self, trade, current_rate, params):
        pass
