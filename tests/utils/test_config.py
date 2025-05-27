from src.utils.config import ConfigLoader
def test_load_method_exists():
    assert hasattr(ConfigLoader, "load")
