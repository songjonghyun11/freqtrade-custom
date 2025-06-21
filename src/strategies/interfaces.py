from abc import ABC, abstractmethod
from typing import Any
from .signal import Signal

class IEntrySignal(ABC):
    @abstractmethod
    def generate(self, ctx: Any, symbol: str, params: dict) -> Signal:
        """롱 진입 신호 생성"""

class IShortSignal(ABC):
    @abstractmethod
    def generate(self, ctx: Any, symbol: str, params: dict) -> Signal:
        """숏 진입 신호 생성"""

class IExitSignal(ABC):
    @abstractmethod
    def generate(self, ctx: Any, symbol: str, params: dict, position: Any = None) -> Signal:
        """청산 신호 생성"""

class IRiskManager(ABC):
    @abstractmethod
    def apply(self, ctx: Any, symbol: str, params: dict, position: Any) -> Any:
        """리스크 평가 및 주문 객체(Order) 리턴"""

# ======== [확장] Allocator & AnomalyDetector 인터페이스 추가 ========

class IAllocator(ABC):
    @abstractmethod
    def decide_allocation(self, ctx: Any, symbol: str, params: dict) -> dict:
        """포지션 배분 결정"""

class IAnomalyDetector(ABC):
    @abstractmethod
    def detect(self, ctx: Any, symbol: str, params: dict) -> bool:
        """이상 감지"""
