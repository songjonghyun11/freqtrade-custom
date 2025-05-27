# src/collectors/interfaces.py

from abc import ABC, abstractmethod

class ICollector(ABC):
    @abstractmethod
    def collect(self, *args, **kwargs):
        """
        데이터를 수집하는 공통 메서드 시그니처를 정의합니다.
        모든 하위 수집기(collector)는 이 메서드를 구현해야 합니다.
        """
        pass
