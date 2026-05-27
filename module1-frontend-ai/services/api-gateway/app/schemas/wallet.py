from pydantic import BaseModel


# wallet structure
class Wallet(BaseModel):
    farmerId: str
    totalCredits: float = 0
    availableCredits: float = 0
    soldCredits: float = 0