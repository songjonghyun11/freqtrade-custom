from typing import List, Dict
from interfaces import IEntrySignal, IShortSignal, IExitSignal, IRiskManager
from mysignal import Signal
from typing import Optional

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

    def decide_long(self, ctx, symbols, params, threshold: float = 0.6) -> Dict:
        results = {}
        for symbol in symbols:
            total_score, total_weight, details = 0.0, 0.0, []

            for signal_obj in self._entries:
                signal = signal_obj.generate(ctx, symbol, params)
                cls_name = signal_obj.__class__.__name__
                weight = params.get("weights", {}).get(cls_name, 1.0)
                weighted_score = signal.score * weight

                total_score += weighted_score
                total_weight += weight
                details.append((cls_name, signal.score, weighted_score))

            avg_score = total_score / total_weight if total_weight > 0 else 0.0
            should_enter = avg_score >= threshold
            results[symbol] = {
                "avg_score": round(avg_score, 4),
                "enter_long": should_enter,
                "details": details
            }

        return results

    def decide_short(self, ctx, symbols, params, threshold: float = 0.6) -> Dict:
        results = {}
        for symbol in symbols:
            total_score, total_weight, details = 0.0, 0.0, []

            for signal_obj in self._shorts:
                signal = signal_obj.generate(ctx, symbol, params)
                cls_name = signal_obj.__class__.__name__
                weight = params.get("weights", {}).get(cls_name, 1.0)
                weighted_score = signal.score * weight

                total_score += weighted_score
                total_weight += weight
                details.append((cls_name, signal.score, weighted_score))

            avg_score = total_score / total_weight if total_weight > 0 else 0.0
            should_short = avg_score >= threshold
            results[symbol] = {
                "avg_score": round(avg_score, 4),
                "enter_short": should_short,
                "details": details
            }

        return results

    def decide_exit(self, ctx, symbols, params, positions, threshold: float = 0.6) -> Dict:
        results = {}
        for symbol in symbols:
            total_score, total_weight, details = 0.0, 0.0, []
            pos = positions.get(symbol)

            for signal_obj in self._exits:
                signal = signal_obj.generate(ctx, symbol, params, pos)
                cls_name = signal_obj.__class__.__name__
                weight = params.get("weights", {}).get(cls_name, 1.0)
                weighted_score = signal.score * weight

                total_score += weighted_score
                total_weight += weight
                details.append((cls_name, signal.score, weighted_score))

            avg_score = total_score / total_weight if total_weight > 0 else 0.0
            should_exit = avg_score >= threshold
            results[symbol] = {
                "avg_score": round(avg_score, 4),
                "exit": should_exit,
                "details": details
            }

        return results

    def assess_risk(self, ctx, symbols, params, positions, threshold: float = 0.6) -> Dict:
        results = {}
        for symbol in symbols:
            total_score, total_weight, details = 0.0, 0.0, []
            pos = positions.get(symbol)

            for manager in self._risks:
                risk_signal = manager.apply(ctx, symbol, params, pos)
                cls_name = manager.__class__.__name__
                weight = params.get("weights", {}).get(cls_name, 1.0)
                score = getattr(risk_signal, 'score', 0.0)
                weighted_score = score * weight

                total_score += weighted_score
                total_weight += weight
                details.append((cls_name, score, weighted_score))

            avg_score = total_score / total_weight if total_weight > 0 else 0.0
            triggered = avg_score >= threshold
            results[symbol] = {
                "avg_score": round(avg_score, 4),
                "risk_triggered": triggered,
                "details": details
            }

        return results
