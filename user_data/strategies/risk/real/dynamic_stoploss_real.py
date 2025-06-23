from interfaces import IRiskManager

class DynamicStoploss(IRiskManager):
    def apply(self, ctx, symbol, params, position):
        entry = position['entry_price']
        price = position['current_price']

        # 심볼별 stoploss 비율, 없으면 2%
        stop_perc = params[symbol].get('stoploss_perc', 0.02)
        stoploss = entry * (1 - stop_perc)

        if price < stoploss:
            return {"action": "close", "reason": "dynamic_stoploss"}
        else:
            return {"action": "hold"}
