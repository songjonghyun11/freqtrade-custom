from src.utils.secrets import SecretLoader
def test_get_method_exists():
    assert hasattr(SecretLoader, "get")
