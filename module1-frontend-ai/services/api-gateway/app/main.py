from fastapi import FastAPI
from app.database import database
from app.routes.activity import router as activity_router
from app.routes.wallet import router as wallet_router
from app.routes.marketplace import router as marketplace_router
from app.routes.transaction import router as transaction_router
from app.routes.auth import router as auth_router
from app.routes.history import router as history

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="EcoChain Bharat API Gateway",
    version="1.0.0"
)

# allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

API_PREFIX = "/api/v1"

app.include_router(
    auth_router,
    prefix=API_PREFIX
)

app.include_router(
    activity_router,
    prefix=API_PREFIX
)

app.include_router(
    transaction_router,
    prefix=API_PREFIX
)

app.include_router(
    wallet_router,
    prefix=API_PREFIX
)

app.include_router(
    history,
    prefix=API_PREFIX
)

app.include_router(
    marketplace_router,
    prefix=API_PREFIX
)

@app.get("/")
async def root():
    return {
        "message": "EcoChain Bharat API Running"
    }

@app.get("/health")
async def health():
    try:
        await database.command("ping")
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }