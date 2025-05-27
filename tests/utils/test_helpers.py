from src.utils.helpers import deep_merge_dicts
def test_deep_merge_signature():
    assert callable(deep_merge_dicts)
