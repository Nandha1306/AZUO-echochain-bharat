from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from app.database import database

from app.services.auth_dependency import (
    get_current_user
)

router = APIRouter(
    prefix="/wallet",
    tags=["Wallet"]
)

# get wallet by owner id
@router.get("/{owner_id}")
async def get_wallet(
    owner_id: str,
    user=Depends(get_current_user)
):
    try:
        wallet = await database.wallets.find_one({
            "ownerId": owner_id
        })

        # wallet not found
        if not wallet:
            raise HTTPException(
                status_code=404,
                detail="Wallet not found"
            )

        # convert mongodb object id
        wallet["_id"] = str(
            wallet["_id"]
        )

        return {
            "success": True,
            "data": wallet
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )