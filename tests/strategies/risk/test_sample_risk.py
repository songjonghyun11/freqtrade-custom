from src.strategies.risk.sample_risk import SampleRisk

def test_generate_signature():
    rm = SampleRisk()
    sig = rm.generate({})
    assert hasattr(sig, "name")
    assert hasattr(sig, "direction")
    assert hasattr(sig, "score")
