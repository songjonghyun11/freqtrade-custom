from pydantic import BaseModel

class Trade(BaseModel):
    id: int
    symbol: str
    price: float
    qty: float

class Reflection(BaseModel):
    id: int
    content: str
    timestamp: str
