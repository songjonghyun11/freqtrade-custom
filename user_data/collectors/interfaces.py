# src/collectors/interfaces.py
from abc import ABC, abstractmethod

class ICollector(ABC):
    @abstractmethod
    def fetch(self, ctx):
        pass
