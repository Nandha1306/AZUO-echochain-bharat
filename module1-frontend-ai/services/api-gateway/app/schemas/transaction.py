from pydantic import BaseModel


# transfer request
class CreditTransfer(BaseModel):
    sellerId: str
    buyerId: str
    credits: float