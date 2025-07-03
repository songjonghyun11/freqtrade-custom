# utils/slippage.py

def estimate_slippage(price, volatility=0.01, liquidity_factor=1.0):
    """
    price: 진입/체결 가격
    volatility: 예측 변동성(1%면 0.01), default 1%
    liquidity_factor: 유동성 영향 (거래량 적으면 >1, 많으면 <1)
    return: slippage(실제 발생할 체결가 차이, float)
    """
    return float(price) * float(volatility) * float(liquidity_factor)

def estimate_slippage_advanced(price, volume, orderbook_depth, volatility=0.01):
    """
    volume: 주문량
    orderbook_depth: 현재 거래소 호가창에 쌓인 물량(동적)
    volatility: 예측 변동성
    """
    if orderbook_depth <= 0:
        orderbook_depth = 1  # 에러 방지
    liquidity_factor = max(1.0, volume / orderbook_depth)
    return float(price) * float(volatility) * liquidity_factor
