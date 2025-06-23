from interfaces import IRiskManagement

class DynamicStoploss(IRiskManagement):
    def __init__(self):
        pass

    def adjust_stoploss(self, trade, current_rate, params):
        # 기본적인 예시 로직 (실제 전략에 따라 수정 가능)
        # 예: 현재가가 3% 이상 수익이면 stoploss를 진입가보다 높게 조정
        entry_rate = trade.open_rate
        profit_ratio = (current_rate - entry_rate) / entry_rate

        if profit_ratio > 0.03:
            return current_rate * 0.98  # 익절 조정
        elif profit_ratio < -0.05:
            return current_rate * 0.97  # 손절 조정
        else:
            return trade.stop_loss  # 그대로 유지
