from src.strategies.short_signals.sample_short import SampleShort

def test_generate_signature():
    ss = SampleShort()
    sig = ss.generate({})
    assert hasattr(sig, "name")
    assert hasattr(sig, "direction")
    assert hasattr(sig, "score")
