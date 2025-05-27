import pytest
from src.collectors.interfaces import ICollector

def test_ICollector_is_abstract():
    """ICollector 클래스가 추상 클래스여야 합니다."""
    with pytest.raises(TypeError):
        ICollector()  # 추상 메서드가 구현되지 않아 TypeError 발생
