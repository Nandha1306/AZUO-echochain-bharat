import httpx
from app.config import BLOCKCHAIN_URL

# register activity on blockchain
async def register_activity_on_blockchain(activity_data):

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{BLOCKCHAIN_URL}/chaincode/registerActivity",
            json=activity_data
        )

        return response.json()


# verify activity on blockchain
async def verify_activity_on_blockchain(activity_data):

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{BLOCKCHAIN_URL}/chaincode/verifyActivity",
            json=activity_data
        )

        return response.json()
    
# mint carbon credits on blockchain
async def mint_credit_on_blockchain(activity_data):

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{BLOCKCHAIN_URL}/chaincode/mintCredit",
            json=activity_data
        )

        return response.json()