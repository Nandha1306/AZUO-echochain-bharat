import httpx

BLOCKCHAIN_URL = "http://127.0.0.1:9000"

async def register_activity_on_blockchain(activity_data):

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{BLOCKCHAIN_URL}/chaincode/registerActivity",
            json=activity_data
        )

        return response.json()