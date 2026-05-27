from fastapi import FastAPI
from datetime import datetime
import random

app = FastAPI(
    title="EcoChain Mock Blockchain",
    version="1.0.0"
)

@app.get("/")
async def root():

    return {
        "message": "Mock Blockchain Running"
    }

@app.post("/chaincode/registerActivity")
async def register_activity(payload: dict):

    tx_id = f"ECBH-2026-{random.randint(10000,99999)}"

    return {
        "txId": tx_id,
        "status": "pending_verification",
        "timestamp": datetime.utcnow().isoformat()
    }