from typing import List
from .interfaces import IEntrySignal, IShortSignal, IExitSignal, IRiskManager
from .signal import Signal

class StrategyOrchestrator:
    def __init__(self,
        entry_signals: List[IEntrySignal],
        short_signals: List[IShortSignal],
        exit_signals: List[IExitSignal],
        risk_managers: List[IRiskManager],
    ):
        self._entries = entry_signals
        self._shorts  = short_signals
        self._exits   = exit_signals
        self._risks   = risk_managers

    def decide_long(self, ctx):
        signals = [s.generate(ctx) for s in self._entries]
        return max(signals, key=lambda x: x.score) if signals else False

    def decide_short(self, ctx):
        signals = [s.generate(ctx) for s in self._shorts]
        return max(signals, key=lambda x: x.score) if signals else False

    def decide_exit(self, ctx):
        signals = [s.generate(ctx) for s in self._exits]
        return max(signals, key=lambda x: x.score) if signals else False

    def assess_risk(self, ctx):
        signals = [s.generate(ctx) for s in self._risks]
        return max(signals, key=lambda x: x.score) if signals else False
