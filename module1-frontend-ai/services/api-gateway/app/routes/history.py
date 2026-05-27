from fastapi import APIRouter
from bson import ObjectId
from app.database import database

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)

# get all transactions
@router.get("")
async def get_all_transactions():
    transactions = []

    async for transaction in database.transactions.find():
        transaction["_id"] = str(transaction["_id"])
        transactions.append(transaction)

    return transactions


# get single transaction
@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: str
):

    transaction = await database.transactions.find_one({
        "_id": ObjectId(transaction_id)
    })

    if not transaction:
        return {
            "message": "Transaction not found"
        }
    
    transaction["_id"] = str(transaction["_id"])

    return transaction

# get farmer transaction history
@router.get("/farmer/{farmer_id}")
async def get_farmer_transactions(
    farmer_id: str
):

    transactions = []

    async for transaction in database.transactions.find({
        "$or": [
            {"sellerId": farmer_id},
            {"buyerId": farmer_id}
        ]
    }):

        transaction["_id"] = str(transaction["_id"])
        transactions.append(transaction)

    return transactions