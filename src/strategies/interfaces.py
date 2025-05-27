# src/strategies/interfaces.py

from abc import ABC, abstractmethod
from typing import Any
from .signal import Signal

class IEntrySignal(ABC):
    @abstractmethod
    def generate(self, ctx: Any) -> Signal:
        """롱 진입 신호 생성"""
        ...

class IShortSignal(ABC):
    @abstractmethod
    def generate(self, ctx: Any) -> Signal:
        """숏 진입 신호 생성"""
        ...

class IExitSignal(ABC):
    @abstractmethod
    def generate(self, ctx: Any) -> Signal:
        """청산 신호 생성"""
        ...

class IRiskManager(ABC):
    @abstractmethod
    def generate(self, ctx: Any) -> Signal:
        """리스크 평가 신호 생성"""
        ...
