from fastapi import APIRouter
from app.database import database

router = APIRouter(
    prefix="/wallet",
    tags=["Wallet"]
)
# get farmer wallet
@router.get("/wallet/{farmer_id}")
async def get_wallet(farmer_id: str):

    wallet = await database.wallets.find_one({
        "farmerId": farmer_id
    })

    # check wallet exists
    if not wallet:

        return {
            "message": "Wallet not found"
        }

    # convert object id to string
    wallet["_id"] = str(wallet["_id"])

    return wallet