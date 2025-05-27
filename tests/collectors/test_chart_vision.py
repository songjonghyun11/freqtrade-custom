from src.collectors.chart_vision import capture_chart

def test_capture_chart_exists():
    """capture_chart 함수가 정의되어 있어야 합니다."""
    assert callable(capture_chart)
