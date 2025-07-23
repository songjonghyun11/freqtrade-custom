# signal_aggregator.py
from typing import List, Dict

class SignalAggregator:

    @staticmethod
    def decide_long(ctx: dict, symbols: list, params: dict, entry_signal_classes: list, threshold: float = 0.6, weighted: bool = False) -> List[Dict]:
        results = []

        for symbol in symbols:
            total_score = 0.0
            total_weight = 0.0
            detail = []

            for Cls in entry_signal_classes:
                instance = Cls()
                signal = instance.generate(ctx, symbol, params)
                weight = getattr(Cls, "weight", 1.0)

                score = signal.score * weight if weighted else signal.score
                total_score += score
                total_weight += weight if weighted else 1.0

                detail.append({
                    "strategy": Cls.__name__,
                    "raw_score": signal.score,
                    "weighted_score": score,
                })

            avg_score = total_score / total_weight if total_weight > 0 else 0.0
            should_enter = avg_score >= threshold

            results.append({
                "symbol": symbol,
                "avg_score": round(avg_score, 4),
                "enter_long": should_enter,
                "details": detail,
            })

        return results

    @staticmethod
    def decide_exit(ctx: dict, symbols: list, params: dict, exit_signal_classes: list, positions: dict, threshold: float = 0.6, weighted: bool = False) -> List[Dict]:
        results = []

        for symbol in symbols:
            total_score = 0.0
            total_weight = 0.0
            detail = []

            position = positions.get(symbol, None)

            for Cls in exit_signal_classes:
                instance = Cls()
                signal = instance.generate(ctx, symbol, params, position)
                weight = getattr(Cls, "weight", 1.0)

                score = signal.score * weight if weighted else signal.score
                total_score += score
                total_weight += weight if weighted else 1.0

                detail.append({
                    "strategy": Cls.__name__,
                    "raw_score": signal.score,
                    "weighted_score": score,
                })

            avg_score = total_score / total_weight if total_weight > 0 else 0.0
            should_exit = avg_score >= threshold

            results.append({
                "symbol": symbol,
                "avg_score": round(avg_score, 4),
                "exit": should_exit,
                "details": detail,
            })

        return results
