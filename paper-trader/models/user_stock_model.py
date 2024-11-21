from dataclasses import dataclass

@dataclass
class UserStock:
    id: int
    user_id: int
    symbol: str
    bought_price: float
    quantity: int