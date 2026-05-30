from pydantic import BaseModel

class Wallet(BaseModel):
    ownerId: str
    ownerType: str
    totalCredits: float = 0
    availableCredits: float = 0
    soldCredits: float = 0