from typing import List, Dict
from interfaces import IEntrySignal, IShortSignal, IExitSignal, IRiskManager
from signal import Signal

class StrategyOrchestrator:
    def __init__(
        self,
        entry_signals: List[IEntrySignal],
        short_signals: List[IShortSignal],
        exit_signals: List[IExitSignal],
        risk_managers: List[IRiskManager],
    ):
        self._entries = entry_signals
        self._shorts  = short_signals
        self._exits   = exit_signals
        self._risks   = risk_managers

    def decide_long(self, ctx, symbols, params):
        results = {}
        for symbol in symbols:
            signals = [s.generate(ctx, symbol, params) for s in self._entries]
            results[symbol] = max(signals, key=lambda x: x.score) if signals else None
        return results

    def decide_short(self, ctx, symbols, params):
        results = {}
        for symbol in symbols:
            signals = [s.generate(ctx, symbol, params) for s in self._shorts]
            results[symbol] = max(signals, key=lambda x: x.score) if signals else None
        return results

    def decide_exit(self, ctx, symbols, params, positions):
        results = {}
        for symbol in symbols:
            signals = [s.generate(ctx, symbol, params, positions.get(symbol)) for s in self._exits]
            results[symbol] = max(signals, key=lambda x: x.score) if signals else None
        return results

    def assess_risk(self, ctx, symbols, params, positions):
        results = {}
        for symbol in symbols:
            signals = [r.apply(ctx, symbol, params, positions.get(symbol)) for r in self._risks]
            results[symbol] = max(signals, key=lambda x: getattr(x, 'score', 0)) if signals else None
        return results
