# tests/performance/test_performance_analyzer.py

from src.performance.performance_analyzer import PerformanceAnalyzer

def test_methods_exist():
    pa = PerformanceAnalyzer()
    assert callable(getattr(pa, "calculate_sharpe", None)), "calculate_sharpe가 없습니다"
    assert callable(getattr(pa, "calculate_max_drawdown", None)), "calculate_max_drawdown이 없습니다"
    assert callable(getattr(pa, "calculate_sortino", None)), "calculate_sortino가 없습니다"
