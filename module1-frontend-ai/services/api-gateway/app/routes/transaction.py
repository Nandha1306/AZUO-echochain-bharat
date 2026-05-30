from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from app.database import database

from app.schemas.transaction import (
    CreditTransfer
)

from app.services.auth_dependency import (
    industry_only
)

from datetime import datetime
from uuid import uuid4

router = APIRouter(
    prefix="/credits",
    tags=["Marketplace"]
)

# transfer carbon credits
@router.post("/transfer")
async def transfer_credits(
    data: CreditTransfer,
    user=Depends(industry_only)
):

    try:
        # get seller wallet
        seller_wallet = await database.wallets.find_one({
            "ownerId": data.sellerId
        })

        # seller wallet not found
        if not seller_wallet:
            raise HTTPException(
                status_code=404,
                detail="Seller wallet not found"
            )

        # insufficient balance
        if seller_wallet["availableCredits"] < data.credits:
            raise HTTPException(
                status_code=400,
                detail="Insufficient credits"
            )

        # reduce seller balance
        await database.wallets.update_one(
            {
                "ownerId": data.sellerId
            },
            {
                "$inc": {
                    "availableCredits": -data.credits,
                    "soldCredits": data.credits
                }
            }
        )

        # check buyer wallet exists
        buyer_wallet = await database.wallets.find_one({
            "ownerId": data.buyerId
        })

        # create buyer wallet if not exists
        if not buyer_wallet:
            buyer_data = {
                "ownerId": data.buyerId,
                "ownerType": "industry",
                "totalCredits": data.credits,
                "availableCredits": data.credits,
                "soldCredits": 0
            }

            await database.wallets.insert_one(
                buyer_data
            )

        # update existing buyer wallet
        else:
            await database.wallets.update_one(
                {
                    "ownerId": data.buyerId
                },
                {
                    "$inc": {
                        "totalCredits": data.credits,
                        "availableCredits": data.credits
                    }
                }
            )

        # create transaction
        transaction = {
            "sellerId": data.sellerId,
            "buyerId": data.buyerId,
            "credits": data.credits,
            "txId": f"TRANSFER-{uuid4()}",
            "timestamp":
                datetime.utcnow().isoformat()
        }

        # save transaction
        result = await database.transactions.insert_one(
            transaction
        )

        transaction["_id"] = str(
            result.inserted_id
        )

        return {
            "success": True,
            "message":
                "Credits transferred successfully",
            "data": {
                "transaction": transaction
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )