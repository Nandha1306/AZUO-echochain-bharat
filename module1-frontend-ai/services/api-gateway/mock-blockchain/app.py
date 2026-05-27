from fastapi import FastAPI
from datetime import datetime
import random

app = FastAPI(
    title="EcoChain Mock Blockchain",
    version="1.0.0"
)

# check mock blockchain service
@app.get("/")
async def root():
    return {
        "message": "Mock Blockchain Running"
    }


# register activity on blockchain
@app.post("/chaincode/registerActivity")
async def register_activity(payload: dict):

    tx_id = f"ECBH-2026-{random.randint(10000,99999)}"

    return {
        "txId": tx_id,
        "status": "pending_verification",
        "timestamp": datetime.utcnow().isoformat()
    }


# verify activity on blockchain
@app.post("/chaincode/verifyActivity")
async def verify_activity(payload: dict):

    tx_id = f"VERIFY-{random.randint(10000,99999)}"

    return {
        "txId": tx_id,
        "status": "verified",
        "verifiedAt": datetime.utcnow().isoformat()
    }

# mint carbon credits on blockchain
@app.post("/chaincode/mintCredit")
async def mint_credit(payload: dict):

    tx_id = f"MINT-{random.randint(10000,99999)}"

    return {
        "txId": tx_id,
        "status": "credits_minted",
        "mintedAt": datetime.utcnow().isoformat()
    }