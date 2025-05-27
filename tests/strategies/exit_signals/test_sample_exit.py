
from src.strategies.exit_signals.sample_exit import SampleExit

def test_generate_signature():
    se = SampleExit()
    sig = se.generate({})
    assert hasattr(sig, "name")
    assert hasattr(sig, "direction")
    assert hasattr(sig, "score")
