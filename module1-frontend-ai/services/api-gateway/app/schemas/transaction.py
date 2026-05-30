from pydantic import BaseModel
from pydantic import field_validator

class CreditTransfer(BaseModel):
    sellerId: str
    buyerId: str
    credits: float

    @field_validator("credits")
    @classmethod
    def validate_credits(cls, value):

        if value <= 0:
            raise ValueError(
                "Credits must be greater than 0"
            )

        return value


    @field_validator("buyerId")
    @classmethod
    def validate_transfer(
        cls,
        buyer_id,
        info
    ):

        seller_id = info.data.get(
            "sellerId"
        )

        if seller_id == buyer_id:
            raise ValueError(
                "Seller and buyer cannot be same"
            )

        return buyer_id