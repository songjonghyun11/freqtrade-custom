from ..interfaces import IExitSignal
from ..signal import Signal, Direction

class ROITargetExitSignal(IExitSignal):
    def generate(self, ctx, position=None):
        # position: {'entry_price': float, 'current_price': float}
        entry = position['entry_price']
        price = position['current_price']

        # 목표수익률 4% (실전에서 최적화 추천)
        if (price - entry) / entry >= 0.04:
            score = 1.0
        else:
            score = 0.0

        return Signal("roi_target_exit", Direction.EXIT, score)

# ---- 실전/주의/보완 ----
# - 목표수익률(4%)은 실전 백테스트/리스크 성향에 따라 조정 필수!
# - 익절만 적용(손절은 따로 리스크 로직과 병행)
# - 급변동장에선 미체결/슬리피지(예상보다 덜 체결) 주의!
# - position dict 반드시 올바른 형태로 전달할 것!
