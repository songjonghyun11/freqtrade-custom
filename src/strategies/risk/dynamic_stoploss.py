from ..interfaces import IRiskManager

class DynamicStoploss(IRiskManager):
    def apply(self, ctx, position):
        # position: {'entry_price': float, 'current_price': float}
        entry = position['entry_price']
        price = position['current_price']

        # 손절(기본 2%): 실전 최적화/변동성/시장 맞춤 조정!
        stoploss = entry * 0.98

        if price < stoploss:
            return {"action": "close", "reason": "dynamic_stoploss"}
        else:
            return {"action": "hold"}

# ---- 실전/주의/보완 ----
# - 손절폭(2%)은 시장/전략별 유연하게 튜닝!
# - 손절만 담당, 익절은 청산로직과 별도 처리
# - position dict 구조 확실하게 맞출 것!
# - 급락/펌핑 등 돌발 변동시 “시장가 강제 청산” 트리거 가능
