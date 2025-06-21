from ..interfaces import IAllocator

class RiskParityAllocator(IAllocator):
    def decide_allocation(self, ctx, symbol, params):
        # 예시: 심볼별 변동성(리스크)로 역가중 배분
        volatility = ctx[symbol].get('volatility', 0.1)
        # 실전에서는 전체 코인 변동성 총합 기준 역가중치 비율 계산
        # 일단 스켈레톤 예시
        allocation = 1.0 / (volatility + 1e-6)  # 변동성 낮을수록 배분↑
        return {
            "symbol": symbol,
            "allocation": allocation
        }
