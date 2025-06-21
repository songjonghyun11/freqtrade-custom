from ..interfaces import IAllocator

class DRLAllocator(IAllocator):
    def decide_allocation(self, ctx, symbol, params):
        # 예시: 강화학습 결과로 symbol별 비중을 리턴
        # 실전에서는 DRL 모델 예측값, 위험 분산 비율 등 활용
        allocation = params[symbol].get('allocation', 1.0)  # 기본값: 100% 배분
        return {
            "symbol": symbol,
            "allocation": allocation  # 0~1, 전체 자본 중 해당 심볼에 몇 % 배분할지
        }
