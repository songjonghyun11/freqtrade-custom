from abc import ABC, abstractmethod

class ICollector(ABC):
    @abstractmethod
    def fetch(self, *args, **kwargs):
        """
        데이터를 fetch해서 반환 (실전/백테스트 모두 지원)
        *args, **kwargs: symbol, timestamp, 기타 파라미터 등 유연하게 대응
        """
        pass
