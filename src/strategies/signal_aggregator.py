# src/strategies/signal_aggregator.py

from typing import List

class SignalAggregator:
    @staticmethod
    def decide_long(ctx: dict) -> List[dict]:
        symbol = ctx.get("symbol", "UNKNOWN")
        return [{"strategy": "mock_long", "symbol": symbol, "score": 0.9}]

    @staticmethod
    def decide_short(ctx: dict) -> List[dict]:
        symbol = ctx.get("symbol", "UNKNOWN")
        return [{"strategy": "mock_short", "symbol": symbol, "score": 0.85}]
