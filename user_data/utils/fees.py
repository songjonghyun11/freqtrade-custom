# utils/fees.py

def calculate_fee(quantity, price, fee_rate=0.001):
    """
    실전/백테스트 모두에서 호출. 수수료 계산.
    quantity: 체결 수량
    price: 체결 가격
    fee_rate: 0.001=0.1% (거래소별/코인별 가변 가능)
    return: fee(수수료, float)
    """
    return float(quantity) * float(price) * float(fee_rate)

def calculate_fee_type(quantity, price, fee_type="taker"):
    """
    fee_type: 'taker' or 'maker'
    """
    fee_rate = 0.001 if fee_type == "taker" else 0.0005
    return float(quantity) * float(price) * float(fee_rate)
