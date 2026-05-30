from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from bson import ObjectId

from app.database import database

from app.services.auth_dependency import (
    get_current_user
)

from app.utils.objectid import (
    validate_object_id
)

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)

# get all transactions
@router.get("")
async def get_all_transactions(
    user=Depends(get_current_user)
):

    try:
        transactions = []

        async for transaction in database.transactions.find():
            transaction["_id"] = str(
                transaction["_id"]
            )
            transactions.append(transaction)

        return {
            "success": True,
            "data": transactions
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# get single transaction
@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: str,
    user=Depends(get_current_user)
):
    try:
        transaction = await database.transactions.find_one({
            "_id": validate_object_id(transaction_id)
        })

        if not transaction:
            raise HTTPException(
                status_code=404,
                detail="Transaction not found"
            )

        transaction["_id"] = str(
            transaction["_id"]
        )

        return {
            "success": True,
            "data": transaction
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# get farmer transaction history
@router.get("/farmer/{farmer_id}")
async def get_farmer_transactions(
    farmer_id: str,
    user=Depends(get_current_user)
):

    try:
        transactions = []

        async for transaction in database.transactions.find({
            "$or": [
                {"sellerId": farmer_id},
                {"buyerId": farmer_id}
            ]
        }):

            transaction["_id"] = str(
                transaction["_id"]
            )

            transactions.append(transaction)

        return {
            "success": True,
            "data": transactions
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )