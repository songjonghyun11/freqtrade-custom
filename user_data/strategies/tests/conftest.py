# tests/conftest.py
import sys, os, types

# 1. Add strategies root to PYTHONPATH
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root)

# 2. Stub freqtrade.strategy and parameters modules
freqtrade_pkg = types.ModuleType('freqtrade')
strategy_pkg  = types.ModuleType('freqtrade.strategy')
params_pkg    = types.ModuleType('freqtrade.strategy.parameters')

# IStrategy stub
class IStrategy:
    def __init__(self, config=None):
        pass
strategy_pkg.IStrategy = IStrategy

# RealParameter stub with .value attribute
class RealParameter:
    def __init__(self, *args, default=None, **kwargs):
        # default if provided, else use minimum bound
        self.value = default if default is not None else args[0]
params_pkg.RealParameter = RealParameter

# IntParameter stub with .value attribute
class IntParameter:
    def __init__(self, *args, default=None, **kwargs):
        self.value = default if default is not None else args[0]
params_pkg.IntParameter = IntParameter

# 3. Stub talib.abstract to allow import
ta_pkg       = types.ModuleType('talib')
abstract_pkg = types.ModuleType('talib.abstract')
sys.modules['talib'] = ta_pkg
sys.modules['talib.abstract'] = abstract_pkg

# 4. Register stub modules
sys.modules['freqtrade'] = freqtrade_pkg
sys.modules['freqtrade.strategy'] = strategy_pkg
sys.modules['freqtrade.strategy.parameters'] = params_pkg