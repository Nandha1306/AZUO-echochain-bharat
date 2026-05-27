from fastapi import APIRouter
from fastapi import Depends
from app.database import database
from app.schemas.transaction import CreditTransfer
from app.services.auth_dependency import industry_only
from datetime import datetime
import random

router = APIRouter(
    prefix="/credits",
    tags=["Marketplace"]
)

# transfer carbon credits
@router.post("/credits/transfer")
async def transfer_credits(
    data: CreditTransfer,
    user=Depends(industry_only)
):

    # get seller wallet
    seller_wallet = await database.wallets.find_one({
        "farmerId": data.sellerId
    })

    # check seller exists
    if not seller_wallet:
        return {
            "message": "Seller wallet not found"
        }

    # check available balance
    if seller_wallet["availableCredits"] < data.credits:
        return {
            "message": "Insufficient credits"
        }

    # reduce seller balance
    await database.wallets.update_one(
        {
            "farmerId": data.sellerId
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
        "farmerId": data.buyerId
    })

    # create buyer wallet if not exists
    if not buyer_wallet:
        buyer_data = {
            "farmerId": data.buyerId,
            "totalCredits": data.credits,
            "availableCredits": data.credits,
            "soldCredits": 0
        }

        await database.wallets.insert_one(buyer_data)

    # update buyer wallet
    else:
        await database.wallets.update_one(
            {
                "farmerId": data.buyerId
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
        "txId": f"TRANSFER-{random.randint(10000,99999)}",
        "timestamp": datetime.utcnow().isoformat()
    }

    result = await database.transactions.insert_one(transaction)

    transaction["_id"] = str(result.inserted_id)

    return {
        "message": "Credits transferred successfully",
        "transaction": transaction
    }