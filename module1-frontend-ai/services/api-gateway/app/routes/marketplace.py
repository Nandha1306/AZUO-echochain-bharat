from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from app.database import database

from app.services.auth_dependency import (
    get_current_user
)

router = APIRouter(
    prefix="/marketplace",
    tags=["Marketplace"]
)

# get marketplace credits
@router.get("")
async def get_marketplace(
    user=Depends(get_current_user)
):

    try:
        marketplace = []

        cursor = database.wallets.find(
            {
                "availableCredits": {
                    "$gt": 0
                }
            },
            {
                "ownerId": 1,
                "ownerType": 1,
                "availableCredits": 1
            }
        )

        async for wallet in cursor:
            wallet["_id"] = str(
                wallet["_id"]
            )

            marketplace.append(wallet)

        return {
            "success": True,
            "data": marketplace
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )