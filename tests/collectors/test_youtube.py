from src.collectors.youtube import fetch_captions

def test_fetch_captions_exists():
    """fetch_captions 함수가 정의되어 있어야 합니다."""
    assert callable(fetch_captions)
