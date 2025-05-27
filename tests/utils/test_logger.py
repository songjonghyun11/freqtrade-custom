from src.utils import logger
def test_setup_logger_exists():
    assert hasattr(logger, "setup_logger")
