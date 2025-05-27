from src.strategies.strategy_orchestrator import StrategyOrchestrator
from src.strategies.entry_signals.fractal_breakout import FractalBreakout
from src.strategies.short_signals.sample_short import SampleShort
from src.strategies.exit_signals.sample_exit import SampleExit
from src.strategies.risk.sample_risk import SampleRisk

def test_orchestrator_methods_exist():
    orchestrator = StrategyOrchestrator(
        [FractalBreakout()], [SampleShort()], [SampleExit()], [SampleRisk()]
    )
    for method in ("decide_long", "decide_short", "decide_exit", "assess_risk"):
        assert callable(getattr(orchestrator, method, None))
