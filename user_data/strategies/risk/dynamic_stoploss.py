from interfaces import IRiskManagement
from pandas import DataFrame

class DynamicStoploss(IRiskManagement):
    def __init__(self, profit_threshold=0.03, stop_threshold=-0.05, profit_sl=0.98, loss_sl=0.97):
        self.profit_threshold = profit_threshold  # 익절 구간 트리거 (하이퍼옵스용)
        self.stop_threshold = stop_threshold      # 손절 구간 트리거 (하이퍼옵스용)
        self.profit_sl = profit_sl                # 익절시 적용할 스톱로스 계수 (하이퍼옵스용)
        self.loss_sl = loss_sl                    # 손절시 적용할 스톱로스 계수 (하이퍼옵스용)

    def adjust_stoploss(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
        entry_rate = trade.open_rate
        profit_ratio = (current_rate - entry_rate) / entry_rate

        if profit_ratio > self.profit_threshold:
            return current_rate * self.profit_sl
        elif profit_ratio < self.stop_threshold:
            return current_rate * self.loss_sl
        else:
            return trade.stop_loss
