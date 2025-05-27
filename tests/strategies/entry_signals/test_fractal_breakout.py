from src.strategies.entry_signals.fractal_breakout import FractalBreakout

def test_generate_signature():
    fb = FractalBreakout()
    sig = fb.generate({})
    assert hasattr(sig, "name")
    assert hasattr(sig, "direction")
    assert hasattr(sig, "score")
