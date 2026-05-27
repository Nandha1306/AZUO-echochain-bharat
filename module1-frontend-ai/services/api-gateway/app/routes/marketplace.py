from fastapi import APIRouter
from app.database import database

router = APIRouter()

# get marketplace credits
@router.get("/marketplace")
async def get_marketplace():

    marketplace = []

    cursor = database.wallets.find({
        "availableCredits": {
            "$gt": 0
        }
    })

    async for wallet in cursor:
        wallet["_id"] = str(wallet["_id"])
        marketplace.append(wallet)

    return marketplace