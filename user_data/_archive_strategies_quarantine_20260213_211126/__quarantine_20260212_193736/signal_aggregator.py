from typing import List, Dict

class SignalAggregator:
    @staticmethod
    def decide_long(ctx: dict, symbols: list, params: dict, entry_signal_classes: list) -> List[Dict]:
        results = []
        for symbol in symbols:
            symbol_scores = []
            for Cls in entry_signal_classes:
                signal = Cls().generate(ctx, symbol, params)
                symbol_scores.append({
                    "strategy": Cls.__name__,
                    "symbol": symbol,
                    "score": signal.score
                })
            # 가장 강한 신호만 기록(원하면 전체도 OK)
            results.append(max(symbol_scores, key=lambda x: x['score']))
        return results

    @staticmethod
    def decide_short(ctx: dict, symbols: list, params: dict, short_signal_classes: list) -> List[Dict]:
        results = []
        for symbol in symbols:
            symbol_scores = []
            for Cls in short_signal_classes:
                signal = Cls().generate(ctx, symbol, params)
                symbol_scores.append({
                    "strategy": Cls.__name__,
                    "symbol": symbol,
                    "score": signal.score
                })
            results.append(max(symbol_scores, key=lambda x: x['score']))
        return results

    @staticmethod
    def decide_exit(ctx: dict, symbols: list, params: dict, exit_signal_classes: list, positions: dict) -> List[Dict]:
        results = []
        for symbol in symbols:
            symbol_scores = []
            position = positions.get(symbol, None)
            for Cls in exit_signal_classes:
                signal = Cls().generate(ctx, symbol, params, position)
                symbol_scores.append({
                    "strategy": Cls.__name__,
                    "symbol": symbol,
                    "score": signal.score
                })
            results.append(max(symbol_scores, key=lambda x: x['score']))
        return results
